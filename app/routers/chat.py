import logging
from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.dependencies import LLMDep, verify_api_key
from app.errors import LLMProviderError, LLMTimeoutError
from app.schemas import ChatRequest, ChatResponse, ResearchAnswer

logger = logging.getLogger(__name__)

STRUCTURED_PROMPT = (
    "คุณเป็นผู้ช่วยวิจัยที่ตอบกระชับ ตรงประเด็น และซื่อสัตย์ "
    "ถ้าไม่แน่ใจหรือข้อมูลอาจล้าสมัย ให้บอกตรง ๆ และตั้ง confidence เป็น low "
    "ตอบเป็นภาษาเดียวกับคำถามของผู้ใช้"
)

STREAM_PROMPT = (
    "คุณเป็นผู้ช่วยวิจัยที่ตอบกระชับ ตรงประเด็น และซื่อสัตย์ "
    "ถ้าไม่แน่ใจให้บอกตรง ๆ ตอบเป็นภาษาเดียวกับคำถามของผู้ใช้"
)

router = APIRouter(
    tags=["chat"],
    dependencies=[Depends(verify_api_key)],
)


def build_messages(system_prompt: str, req: ChatRequest) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": system_prompt}]
    messages += [m.model_dump() for m in req.messages]
    return messages


@router.post("/chat", summary="ถามคำถามและได้คำตอบแบบมีโครงสร้าง")
async def chat(req: ChatRequest, llm: LLMDep) -> ChatResponse:
    """
    ส่งประวัติการสนทนาเข้ามา แล้วได้คำตอบที่มี
    **summary**, **key_points**, **confidence** และ **follow_up_questions**

    - ต้องส่ง header `X-API-Key`
    - คืน **504** ถ้า LLM ตอบช้าเกินกำหนด และ **502** ถ้า LLM ขัดข้อง
    """
    answer = await llm.ask_structured(build_messages(STRUCTURED_PROMPT, req), ResearchAnswer)
    return ChatResponse(answer=answer, model=llm.model)


@router.post(
    "/chat/stream",
    response_class=EventSourceResponse,
    summary="ถามคำถามและรับคำตอบทีละส่วน (SSE)",
)
async def chat_stream(req: ChatRequest, llm: LLMDep) -> AsyncIterable[ServerSentEvent]:
    """
    ส่งคำตอบกลับเป็น Server-Sent Events:

    - `token` — ข้อความทีละส่วน
    - `error` — เกิดปัญหาระหว่างทาง (มี `code` และ `message`)
    - `done` — จบคำตอบ
    """
    try:
        async for token in llm.stream_text(build_messages(STREAM_PROMPT, req)):
            yield ServerSentEvent(data=token, event="token")
    except LLMTimeoutError as e:
        logger.warning("LLM timeout during stream: %s", e)
        yield ServerSentEvent(
            data={"code": "LLM_TIMEOUT", "message": "ระบบ AI ตอบช้าเกินกำหนด กรุณาลองใหม่"},
            event="error",
        )
        return
    except LLMProviderError as e:
        logger.error("LLM provider error during stream: %s", e)
        yield ServerSentEvent(
            data={"code": "LLM_UNAVAILABLE", "message": "ระบบ AI ขัดข้องชั่วคราว กรุณาลองใหม่"},
            event="error",
        )
        return

    yield ServerSentEvent(raw_data="[DONE]", event="done")