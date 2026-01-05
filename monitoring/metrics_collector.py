import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from threading import Lock
from datetime import datetime


@dataclass
class MetricsData:
    """Container for application metrics."""

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Token usage metrics
    total_stt_tokens: int = 0  # Deepgram audio duration in seconds
    total_llm_input_tokens: int = 0  # Bedrock input tokens
    total_llm_output_tokens: int = 0  # Bedrock output tokens

    # Latency metrics
    total_latency_ms: float = 0.0
    request_count_for_latency: int = 0

    # Session metrics
    active_sessions: int = 0
    total_sessions: int = 0

    # Service start time
    start_time: float = field(default_factory=time.time)

    def get_average_latency(self) -> float:
        """Calculate average latency."""
        if self.request_count_for_latency == 0:
            return 0.0
        return self.total_latency_ms / self.request_count_for_latency

    def get_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def get_uptime_seconds(self) -> int:
        """Get service uptime in seconds."""
        return int(time.time() - self.start_time)

    def estimate_cost(self) -> Dict[str, float]:
        """Estimate costs based on token usage."""
        # Approximate pricing (update with actual rates)
        deepgram_cost_per_minute = 0.0125  # $0.0125 per minute
        bedrock_input_cost_per_1k = 0.003  # $0.003 per 1K input tokens (Claude Sonnet)
        bedrock_output_cost_per_1k = 0.015  # $0.015 per 1K output tokens

        deepgram_minutes = self.total_stt_tokens / 60  # Convert seconds to minutes
        deepgram_cost = deepgram_minutes * deepgram_cost_per_minute

        bedrock_input_cost = (
            self.total_llm_input_tokens / 1000
        ) * bedrock_input_cost_per_1k
        bedrock_output_cost = (
            self.total_llm_output_tokens / 1000
        ) * bedrock_output_cost_per_1k

        return {
            "deepgram_usd": round(deepgram_cost, 4),
            "bedrock_input_usd": round(bedrock_input_cost, 4),
            "bedrock_output_usd": round(bedrock_output_cost, 4),
            "total_usd": round(
                deepgram_cost + bedrock_input_cost + bedrock_output_cost, 4
            ),
        }


class MetricsCollector:
    """Thread-safe metrics collector."""

    def __init__(self):
        self._metrics = MetricsData()
        self._lock = Lock()

    def record_request(self, success: bool, latency_ms: float):
        """Record a request with its outcome and latency."""
        with self._lock:
            self._metrics.total_requests += 1
            if success:
                self._metrics.successful_requests += 1
            else:
                self._metrics.failed_requests += 1

            self._metrics.total_latency_ms += latency_ms
            self._metrics.request_count_for_latency += 1

    def record_stt_usage(self, audio_duration_seconds: float):
        """Record STT usage (Deepgram audio duration)."""
        with self._lock:
            self._metrics.total_stt_tokens += int(audio_duration_seconds)

    def record_llm_usage(self, input_tokens: int, output_tokens: int):
        """Record LLM token usage."""
        with self._lock:
            self._metrics.total_llm_input_tokens += input_tokens
            self._metrics.total_llm_output_tokens += output_tokens

    def increment_active_sessions(self):
        """Increment active session count."""
        with self._lock:
            self._metrics.active_sessions += 1
            self._metrics.total_sessions += 1

    def decrement_active_sessions(self):
        """Decrement active session count."""
        with self._lock:
            self._metrics.active_sessions = max(0, self._metrics.active_sessions - 1)

    def get_metrics(self) -> Dict:
        """Get current metrics snapshot."""
        with self._lock:
            return {
                "total_requests": self._metrics.total_requests,
                "successful_requests": self._metrics.successful_requests,
                "failed_requests": self._metrics.failed_requests,
                "total_tokens_stt": self._metrics.total_stt_tokens,
                "total_tokens_llm_input": self._metrics.total_llm_input_tokens,
                "total_tokens_llm_output": self._metrics.total_llm_output_tokens,
                "average_latency_ms": self._metrics.get_average_latency(),
                "error_rate": self._metrics.get_error_rate(),
                "uptime_seconds": self._metrics.get_uptime_seconds(),
                "active_sessions": self._metrics.active_sessions,
                "total_sessions": self._metrics.total_sessions,
                "estimated_costs": self._metrics.estimate_cost(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._metrics = MetricsData()


# Global metrics collector instance
metrics_collector = MetricsCollector()
