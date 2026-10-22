import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.services.llm import GroqClient

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_llm(settings: SettingsDep) -> GroqClient:
    return GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        timeout=settings.llm_timeout_seconds,
    )


LLMDep = Annotated[GroqClient, Depends(get_llm)]


def verify_api_key(
    settings: SettingsDep,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.app_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_API_KEY", "message": "API key ไม่ถูกต้อง"},
        )