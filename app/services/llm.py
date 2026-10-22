from collections.abc import AsyncIterator
from typing import TypeVar

from groq import APIError, APITimeoutError, AsyncGroq
from pydantic import BaseModel, ValidationError

from app.errors import LLMProviderError, LLMTimeoutError

T = TypeVar("T", bound=BaseModel)


class GroqClient:
    def __init__(self, api_key: str, model: str, timeout: float):
        self._client = AsyncGroq(api_key=api_key, timeout=timeout)
        self.model = model

    async def ask_structured(self, messages: list[dict[str, str]], schema: type[T]) -> T:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    },
                },
            )
        except APITimeoutError as e:
            raise LLMTimeoutError("groq") from e
        except APIError as e:
            raise LLMProviderError("groq", str(e)) from e

        content = response.choices[0].message.content
        try:
            return schema.model_validate_json(content)
        except ValidationError as e:
            raise LLMProviderError("groq", f"invalid structured output: {e}") from e

    async def stream_text(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APITimeoutError as e:
            raise LLMTimeoutError("groq") from e
        except APIError as e:
            raise LLMProviderError("groq", str(e)) from e