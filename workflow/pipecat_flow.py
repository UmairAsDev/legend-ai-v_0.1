import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


load_dotenv(override=True)

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import settings

logger.add("logs/pipecat_flow.log", rotation="100 MB", enqueue=True)


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

    def add(self, text: str):
        if text and text.strip():
            self.parts.append(text.strip())

    def full_text(self) -> str:
        return " ".join(self.parts)

    def clear(self):
        self.parts.clear()


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting medical dictation pipeline")

    # STT
    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)

    # LLM (AWS Bedrock)
    llm = AWSBedrockLLMService(model=settings.model_id, aws_region='us-east-1')

    transcript_buffer = TranscriptBuffer()


    @stt.event_handler("on_final_transcript")
    async def on_final_transcript(service, transcript, **kwargs):
        transcript_buffer.add(transcript)

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

    async def generate_soap_note():
        transcript = transcript_buffer.full_text()

        if not transcript:
            logger.warning("No transcript captured")
            return

        logger.info("Generating SOAP note")

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

        await llm(context) #type: ignore

        logger.info("SOAP note generated successfully")

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
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=0.4)
            ),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=0.4)
            ),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)




if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
