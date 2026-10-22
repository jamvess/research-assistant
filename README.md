# Research Assistant API

A FastAPI service that answers research questions using an LLM on Groq. It returns either a **structured answer** (summary, key points, confidence, follow-up questions) or a **streamed answer** over Server-Sent Events.

## Features

- `POST /chat` returns a structured answer validated against a Pydantic schema (Groq strict JSON schema mode)
- `POST /chat/stream` streams the answer token by token with Server-Sent Events
- API key authentication on all chat endpoints, with a public `/health` endpoint
- LLM failures mapped to clear HTTP errors: **504** on timeout, **502** on provider errors
- Errors during streaming are sent as an `error` event, since the status code has already been sent
- Test suite that runs without calling the real LLM, using FastAPI dependency overrides
- Runs locally with `uv` or in Docker with one command

## Tech stack

Python 3.12 · FastAPI · Pydantic v2 · pydantic-settings · Groq (`openai/gpt-oss-20b`) · pytest · Docker · uv

## Project structure

```
app/
├── main.py            # App setup: routers and error handlers
├── config.py          # Settings loaded from environment variables
├── dependencies.py    # get_llm, verify_api_key
├── errors.py          # LLM exceptions and their HTTP handlers
├── schemas.py         # Request/response models and the LLM output schema
├── routers/
│   ├── chat.py        # /chat and /chat/stream
│   └── health.py      # /health
└── services/
    └── llm.py         # Groq client: structured output and streaming
tests/
├── conftest.py        # Fake LLMs and test fixtures
└── test_chat.py
```

## Getting started

### 1. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Your key from [console.groq.com](https://console.groq.com) |
| `APP_API_KEY` | Yes | The key clients must send in the `X-API-Key` header |
| `GROQ_MODEL` | No | Defaults to `openai/gpt-oss-20b` |
| `LLM_TIMEOUT_SECONDS` | No | Defaults to `30` |

### 2a. Run with Docker

```bash
docker compose up --build
```

### 2b. Or run locally with uv

```bash
uv sync
uv run fastapi dev
```

Open the interactive docs at http://127.0.0.1:8000/docs

## Usage

Structured answer:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-app-api-key" \
  -d '{"messages": [{"role": "user", "content": "What is RAG and how is it different from fine-tuning?"}]}'
```

Example response:

```json
{
  "answer": {
    "summary": "RAG retrieves relevant documents at query time and passes them to the model ...",
    "key_points": ["...", "...", "..."],
    "confidence": "high",
    "follow_up_questions": ["...", "..."]
  },
  "model": "openai/gpt-oss-20b"
}
```

Streaming answer:

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-app-api-key" \
  -d '{"messages": [{"role": "user", "content": "Explain RAG briefly"}]}'
```

The stream sends `token` events, then a `done` event. If the LLM fails mid-stream, it sends an `error` event with a `code` and `message`.

## Testing

```bash
uv run pytest -v
```

Tests replace the real LLM with fakes through `app.dependency_overrides`, so they run fast, cost nothing, and can simulate failures such as timeouts.

## Design decisions

- **System prompt stays on the server.** Clients can only send `user` and `assistant` messages, so they cannot override the assistant's instructions.
- **Provider errors are translated at the service layer.** `services/llm.py` converts Groq exceptions into `LLMTimeoutError` and `LLMProviderError`, so the rest of the app does not depend on Groq. Adding another provider only requires a new client class.
- **LLM output is validated twice.** Groq's strict mode enforces the JSON schema, and Pydantic validates the result again before it is returned.
- **Secrets never enter the Docker image.** `.env` is excluded by `.dockerignore` and passed in at runtime through `env_file`.
- **Input limits control cost.** Messages are limited to 4,000 characters and conversations to 20 messages.

## Next steps

- Retrieval over uploaded documents (RAG)
- Tracing and evaluation of answer quality
- Rate limiting per API key