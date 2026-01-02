import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from loguru import logger

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams  
from pipecat.observers.loggers.llm_log_observer import LLMLogObserver
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import LLMRunFrame

     

# Custom imports from your project
from config.settings import settings
from prompt import CLINICAL_SYSTEM_PROMPT

load_dotenv(override=True)
logger.add("logs/bot.log", rotation="100 MB", enqueue=True)





from pipecat.frames.frames import LLMFullResponseEndFrame, TextFrame

async def main():
    transport = LocalAudioTransport(
        params=LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,  # No TTS output needed
            vad_analyzer=SileroVADAnalyzer(),
        )
    )

    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)
    
    llm = AWSBedrockLLMService(
        model=settings.model_id,
        region=settings.region
    )

    # Context with proper message format
    message = [{
    "role": "system",
    "content": (
        "You are a clinical transcription assistant. Your goal is to convert doctor dictations into structured JSON notes. "
        "1. Correct transcription errors intelligently (e.g., 'iron olecranon' -> 'isotretinoin'). "
        "2. Output ONLY a JSON object with these keys: past_medical_history, allergies, current_medication, "
        "review_of_system, history_of_present_illness, examination, assessment_and_plan, procedure, icdCodes, cptCodes. "
        "3. Use HTML for the values. Do NOT include section headings inside the HTML strings. "
        "4. Bold and underline diagnosis names. No bullet points or numbering. "
        "5. Include correct ICD and CPT codes. "
        "6. If insufficient data exists, return {'error': 'Insufficient or unrelated content'}. "
        "7. Format style: Focused, Comprehensive, or Categorized as requested in the transcript."
    )
    }]
    context = LLMContext(messages=message) #type:ignore
    context_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        # No TTS - LLM text output goes directly downstream
        context_aggregator.assistant(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            observers=[LLMLogObserver()],
        )
    )
    
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())