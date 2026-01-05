import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
import time
import json


load_dotenv(override=True)

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import settings
from monitoring.metrics_collector import metrics_collector
from monitoring.logger import get_logger, configure_logging
from utils.validators import (
    validate_transcript,
    validate_clinical_note_response,
    extract_json_from_response,
)
from utils.retry_handler import retry_with_backoff

# Configure structured logging
configure_logging(log_level="INFO", log_file="logs/pipecat_flow.log")
logger = get_logger()


from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import (
    LocalSmartTurnAnalyzerV3,
)

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

from pipecat.processors.frameworks.rtvi import (
    RTVIProcessor,
    RTVIConfig,
    RTVIObserver,
)

from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.aws.llm import AWSBedrockLLMService

from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams


SYSTEM_PROMPT = """
You are a clinical documentation assistant.
Generate a SOAP note from the transcript.
Do NOT add diagnoses or facts not explicitly stated.
Use concise, professional medical language.
"""


class TranscriptBuffer:
    def __init__(self):
        self.parts = []
        self.audio_duration = 0.0  # Track audio duration for metrics
        self.start_time = time.time()

    def add(self, text: str):
        if text and text.strip():
            self.parts.append(text.strip())

    def full_text(self) -> str:
        return " ".join(self.parts)

    def get_duration(self) -> float:
        """Get session duration in seconds."""
        return time.time() - self.start_time

    def clear(self):
        self.parts.clear()
        self.audio_duration = 0.0


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting medical dictation pipeline")

    # STT
    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)

    # LLM (AWS Bedrock)
    llm = AWSBedrockLLMService(model=settings.model_id, aws_region="us-east-1")

    transcript_buffer = TranscriptBuffer()

    @stt.event_handler("on_final_transcript")
    async def on_final_transcript(service, transcript, **kwargs):
        """Handle final transcript from STT service."""
        transcript_buffer.add(transcript)
        logger.debug(f"Received transcript: {len(transcript)} characters")

        # Track audio duration if available in kwargs
        if "duration" in kwargs:
            duration = kwargs["duration"]
            transcript_buffer.audio_duration += duration
            metrics_collector.record_stt_usage(duration)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # PIPELINE: Audio → STT only
    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
        ]
    )

    task = PipelineTask(
        pipeline=pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    async def generate_soap_note():
        """Generate SOAP note from transcript with error handling and metrics."""
        transcript = transcript_buffer.full_text()

        # Validate transcript
        if not validate_transcript(transcript):
            logger.error("Invalid or empty transcript")
            return {"error": "Insufficient or invalid transcript content"}

        logger.info(f"Generating SOAP note from transcript ({len(transcript)} chars)")

        # Track session duration
        session_duration = transcript_buffer.get_duration()
        logger.info(f"Session duration: {session_duration:.2f}s")

        context = LLMContext(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""
                Transcript:
                {transcript}

                Generate a SOAP note with:
                Subjective:
                Objective:
                Assessment:
                Plan:
                """,
                },
            ]
        )

        try:
            # Call LLM and track token usage
            llm_start = time.time()
            result = await llm(context)  # type: ignore
            llm_latency = (time.time() - llm_start) * 1000

            logger.info(f"LLM response received in {llm_latency:.2f}ms")

            # Extract token usage from result if available
            if hasattr(result, "usage"):
                input_tokens = getattr(result.usage, "input_tokens", 0)
                output_tokens = getattr(result.usage, "output_tokens", 0)
                metrics_collector.record_llm_usage(input_tokens, output_tokens)
                logger.info(
                    f"Token usage - Input: {input_tokens}, Output: {output_tokens}"
                )

            # Validate response
            if hasattr(result, "content"):
                response_text = result.content
                try:
                    response_json = extract_json_from_response(response_text)
                    if validate_clinical_note_response(response_json):
                        logger.info("SOAP note generated successfully")
                        return response_json
                    else:
                        logger.warning("Generated note failed validation")
                        return {"error": "Generated note has insufficient content"}
                except Exception as e:
                    logger.error(f"Failed to parse LLM response: {str(e)}")
                    return {"error": "Failed to parse clinical note"}

            logger.info("SOAP note generated successfully")
            return result

        except Exception as e:
            logger.error(f"Error generating SOAP note: {str(e)}")
            raise

    @transport.event_handler("on_stop")
    async def on_stop():
        logger.info("Session ended — finalizing note")
        await generate_soap_note()
        transcript_buffer.clear()
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.4)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.4)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
