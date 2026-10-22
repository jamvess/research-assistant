import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class LLMTimeoutError(Exception):
    def __init__(self, provider: str):
        super().__init__(f"{provider} timed out")
        self.provider = provider


class LLMProviderError(Exception):
    def __init__(self, provider: str, message: str):
        super().__init__(f"{provider} error: {message}")
        self.provider = provider
        self.message = message


async def llm_timeout_handler(request: Request, exc: LLMTimeoutError) -> JSONResponse:
    logger.warning("LLM timeout: provider=%s path=%s", exc.provider, request.url.path)
    return JSONResponse(
        status_code=504,
        content={"code": "LLM_TIMEOUT", "message": "ระบบ AI ตอบช้าเกินกำหนด กรุณาลองใหม่"},
    )


async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
    logger.error("LLM provider error: provider=%s message=%s", exc.provider, exc.message)
    return JSONResponse(
        status_code=502,
        content={"code": "LLM_UNAVAILABLE", "message": "ระบบ AI ขัดข้องชั่วคราว กรุณาลองใหม่"},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(LLMTimeoutError, llm_timeout_handler)
    app.add_exception_handler(LLMProviderError, llm_provider_error_handler)