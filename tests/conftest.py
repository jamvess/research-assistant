import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_llm
from app.errors import LLMTimeoutError
from app.main import app
from app.schemas import ResearchAnswer

TEST_API_KEY = "test-key"


class FakeLLM:
    model = "fake-model"

    async def ask_structured(self, messages, schema):
        return ResearchAnswer(
            summary="คำตอบปลอม",
            key_points=["a", "b", "c"],
            confidence="high",
            follow_up_questions=["x", "y"],
        )

    async def stream_text(self, messages):
        for token in ["สวัส", "ดี", "ครับ"]:
            yield token


class TimeoutLLM(FakeLLM):
    async def ask_structured(self, messages, schema):
        raise LLMTimeoutError("fake")

    async def stream_text(self, messages):
        yield "ตอบได้ครึ่งเดียว"
        raise LLMTimeoutError("fake")


def get_test_settings() -> Settings:
    return Settings(groq_api_key="not-used", app_api_key=TEST_API_KEY)


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_llm] = lambda: FakeLLM()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def timeout_llm(client):
    app.dependency_overrides[get_llm] = lambda: TimeoutLLM()


@pytest.fixture
def auth_headers():
    return {"X-API-Key": TEST_API_KEY}