# Legend Voice Agent

Production-ready voice-to-clinical-note API with comprehensive monitoring, error handling, and security features.

## Features

- 🎤 **Voice Transcription**: Real-time speech-to-text using Deepgram
- 🤖 **AI-Powered**: Clinical note generation using AWS Bedrock (Claude)
- 📊 **Comprehensive Monitoring**: Token usage tracking, cost estimation, and performance metrics
- 🔒 **Security**: API key authentication, rate limiting, input validation
- 🛡️ **Resilience**: Circuit breakers, retry logic with exponential backoff
- 📝 **Structured Logging**: Correlation IDs for request tracing, PII sanitization
- 🏥 **HIPAA-Ready**: Audit logging, data encryption support

## Quick Start

### Prerequisites

- Python 3.10
- Docker (optional, for containerized deployment)
- Deepgram API key
- AWS credentials with Bedrock access

### Local Development

1. **Clone the repository**
   ```bash
   cd /home/umair/projects/legend-voice-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Metrics: http://localhost:8000/metrics

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

## API Endpoints

### Health Check
```bash
GET /health
```

Returns service health status and external service connectivity.

### Metrics
```bash
GET /metrics
```

Returns comprehensive metrics including:
- Total requests and error rates
- Token usage (STT and LLM)
- Cost estimates
- Average latency
- Active sessions

### Generate Clinical Note
```bash
POST /api/v1/bot
Content-Type: application/json
X-API-Key: your-api-key

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

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_KEYS` | Comma-separated list of valid API keys | - | No* |
| `DEEPGRAM_API_KEY` | Deepgram API key for STT | - | Yes |
| `AWS_REGION` | AWS region for Bedrock | us-east-1 | Yes |
| `MODEL_ID` | AWS Bedrock model ID | - | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | - | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | Yes |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per client | 60 | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO | No |
| `ENVIRONMENT` | Environment (development/production) | development | No |
| `HOST` | Server host | 127.0.0.1 | No |
| `PORT` | Server port | 8000 | No |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | * | No |

\* API key authentication is optional but recommended for production

## Monitoring & Metrics

The API tracks comprehensive metrics accessible via `/metrics`:

- **Token Usage**: Real-time tracking of Deepgram and Bedrock token consumption
- **Cost Estimation**: Automatic cost calculation based on current pricing
- **Performance**: Request latency, throughput, error rates
- **Sessions**: Active and total session counts

### Example Metrics Response
```json
{
  "total_requests": 150,
  "total_tokens_stt": 45000,
  "total_tokens_llm_input": 12000,
  "total_tokens_llm_output": 8000,
  "average_latency_ms": 2500.5,
  "error_rate": 1.2,
  "uptime_seconds": 86400,
  "estimated_costs": {
    "deepgram_usd": 9.375,
    "bedrock_input_usd": 0.036,
    "bedrock_output_usd": 0.12,
    "total_usd": 9.531
  }
}
```

## Error Handling

The API implements comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff for transient failures
- **Circuit Breakers**: Prevents cascading failures from external services
- **Validation**: Input validation with detailed error messages
- **Logging**: All errors logged with correlation IDs for tracing

## Security Features

- **API Key Authentication**: Header-based authentication (`X-API-Key`)
- **Rate Limiting**: Per-client rate limiting (default: 60 requests/minute)
- **Input Sanitization**: Automatic sanitization of user inputs
- **PII Protection**: Sensitive data redacted in logs
- **CORS**: Configurable CORS policies

## Project Structure

```
legend-voice-agent/
├── controller/          # API routes and request handlers
│   ├── route/          # API endpoints
│   └── schemas/        # Pydantic models for validation
├── middleware/         # Custom middleware
│   ├── auth.py        # API key authentication
│   ├── rate_limiter.py # Rate limiting
│   ├── error_handler.py # Global error handling
│   └── logging_middleware.py # Request logging
├── monitoring/         # Monitoring and observability
│   ├── metrics_collector.py # Metrics tracking
│   └── logger.py      # Structured logging
├── utils/             # Utility functions
│   ├── retry_handler.py # Retry logic and circuit breakers
│   └── validators.py  # Input validation
├── workflow/          # Core business logic
│   ├── pipecat_flow.py # Main voice processing workflow
│   ├── prompt.py      # LLM prompts
│   └── bot.py         # Alternative bot implementation
├── config/            # Configuration
├── logs/              # Application logs
├── main.py            # Application entry point
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose setup
├── requirements.txt   # Python dependencies
└── .env.example       # Environment variables template
```

## Development

### Running Tests
```bash
pytest tests/ -v --cov=.
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## Troubleshooting

### Common Issues

**1. Import Errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

**2. AWS Bedrock Access Denied**
- Verify AWS credentials are correct
- Ensure IAM role has Bedrock permissions
- Check if model is available in your region

**3. Deepgram API Errors**
- Verify API key is valid
- Check Deepgram account balance
- Review rate limits

**4. High Latency**
- Check network connectivity to AWS/Deepgram
- Review circuit breaker status in logs
- Monitor token usage and costs

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub or contact [your-email@example.com]
