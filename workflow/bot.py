import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from loguru import logger

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
)
from pipecat.transports.local.audio import (
    LocalAudioTransport,
    LocalAudioTransportParams,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.observers.loggers.llm_log_observer import LLMLogObserver
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.runner import PipelineRunner
from config.settings import settings
from workflow.prompt import prompt_with_context

load_dotenv(override=True)
logger.add("logs/bot.log", rotation="100 MB", enqueue=True)


async def main(patient_data: dict):
    transport = LocalAudioTransport(
        params=LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            vad_analyzer=SileroVADAnalyzer(),
        )
    )

    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)

    llm = AWSBedrockLLMService(model=settings.model_id, region=settings.region)

    system_prompt = prompt_with_context(patient_data)

    messages = [system_prompt, {"role": "user", "content": patient_data}]

    context = LLMContext(messages=messages)  # type:ignore
    context_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            observers=[LLMLogObserver()],
        ),
    )

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    patient_data = {"": ""}
    asyncio.run(main(patient_data))
