# Legend Voice Agent - Updated for Pipecat Native Monitoring

Production-ready voice-to-clinical-note API with **Pipecat's native OpenTelemetry tracing** for comprehensive monitoring.

## Key Changes

✅ **Removed custom authentication** - Your integrating system handles this  
✅ **Using Pipecat's native metrics** - OpenTelemetry tracing for token usage, latency, and performance  
✅ **Simplified architecture** - No redundant metrics collection  
✅ **Optional rate limiting** - Set `RATE_LIMIT_PER_MINUTE=0` to disable  

## Features

- 🎤 **Voice Transcription**: Real-time speech-to-text using Deepgram
- 🤖 **AI-Powered**: Clinical note generation using AWS Bedrock (Claude)
- 📊 **Pipecat Native Monitoring**: OpenTelemetry tracing with automatic token usage tracking
- 🛡️ **Resilience**: Circuit breakers, retry logic with exponential backoff
- 📝 **Structured Logging**: Correlation IDs for request tracing, PII sanitization

## Quick Start

### Prerequisites

- Python 3.10
- Docker (optional, for containerized deployment)
- Deepgram API key
- AWS credentials with Bedrock access
- OpenTelemetry Collector (optional, for metrics)

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Run the application**
   ```bash
   python3 main.py
   ```

4. **Access the API**
   - API: http://localhost:8001
   - Swagger Docs: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

## OpenTelemetry Tracing Setup

Pipecat automatically tracks:
- **Token Usage**: Deepgram (STT) and AWS Bedrock (LLM) token consumption
- **Latency**: Request processing times
- **Turns**: Conversation turn tracking
- **Errors**: Automatic error capture

### Enable Tracing

```bash
# In .env file
OTEL_TRACING_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317  # Your collector endpoint
OTEL_CONSOLE_EXPORT=false  # Set true for debug output
```

### Jaeger Example

```bash
# Run Jaeger all-in-one
docker run -d --name jaeger \
  -p 4317:4317 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI at http://localhost:16686
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEEPGRAM_API_KEY` | Deepgram API key for STT | - | Yes |
| `AWS_REGION` | AWS region for Bedrock | us-east-1 | Yes |
| `MODEL_ID` | AWS Bedrock model ID | - | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | - | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | Yes |
| `OTEL_TRACING_ENABLED` | Enable OpenTelemetry tracing | false | No |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | http://localhost:4317 | No |
| `OTEL_CONSOLE_EXPORT` | Export traces to console | false | No |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per client (0=disabled) | 0 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `ENVIRONMENT` | Environment (development/production) | development | No |
| `HOST` | Server host | 127.0.0.1 | No |
| `PORT` | Server port | 8001 | No |

## API Endpoints

### Health Check
```bash
GET /health
```

### Metrics Info
```bash
GET /metrics
```
Returns information about OpenTelemetry tracing. Actual metrics are in your OTLP backend.

### Generate Clinical Note
```bash
POST /api/v1/bot
Content-Type: application/json

{
  "patient_data": {
    "patient_id": "12345",
    "name": "John Doe",
    "age": 45
  },
  "config": {
    "note_style": "comprehensive",
    "include_icd_codes": true,
    "include_cpt_codes": true
  }
}
```

## Monitoring with OpenTelemetry

Pipecat automatically exports:

- **Spans**: Request traces with timing
- **Metrics**: Token counts, latencies, error rates
- **Attributes**: Session IDs, conversation IDs, service metadata

Query your OpenTelemetry backend (Jaeger, Prometheus, etc.) for:
- Token usage trends
- Cost analysis
- Performance bottlenecks
- Error tracking

## Project Structure

```
legend-voice-agent/
├── controller/          # API routes
├── middleware/         # Logging, rate limiting, error handling
├── monitoring/         # Structured logging
├── utils/             # Validators, retry logic, circuit breakers
├── workflow/          # Pipecat voice processing with OpenTelemetry
├── config/            # Configuration
├── main.py            # Application entry point
└── requirements.txt   # Dependencies (includes OpenTelemetry)
```

## What Changed

### Removed
- ❌ Custom metrics collector
- ❌ API key authentication (handled by your system)
- ❌ Manual token tracking

### Added
- ✅ Pipecat native OpenTelemetry tracing
- ✅ Automatic token usage tracking
- ✅ Conversation and turn tracking
- ✅ Configurable OTLP export

### Kept
- ✅ Error handling & circuit breakers
- ✅ Retry logic with exponential backoff
- ✅ Input validation
- ✅ Structured logging with correlation IDs
- ✅ Optional rate limiting

## Development

### Running Tests
```bash
pytest tests/ -v
```

## Troubleshooting

**OpenTelemetry not working?**
- Verify `OTEL_TRACING_ENABLED=true` in .env
- Check collector is running on configured endpoint
- Enable console export for debugging: `OTEL_CONSOLE_EXPORT=true`

**High latency?**
- Check OpenTelemetry traces for bottlenecks
- Review circuit breaker status in logs
- Monitor AWS/Deepgram service health

## License

[Your License Here]
