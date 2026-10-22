from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ResearchAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="สรุปคำตอบ 2-3 ประโยค ใช้ภาษาเดียวกับคำถาม")
    key_points: list[str] = Field(description="ประเด็นสำคัญ 3-5 ข้อ")
    confidence: Literal["low", "medium", "high"] = Field(
        description="ความมั่นใจในคำตอบ ให้ตอบ low ถ้าไม่แน่ใจหรือข้อมูลอาจล้าสมัย"
    )
    follow_up_questions: list[str] = Field(description="คำถามต่อยอดที่น่าสนใจ 2 ข้อ")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(
        min_length=1,
        max_length=20,
        description="ประวัติการสนทนา เรียงจากเก่าไปใหม่ ข้อความสุดท้ายต้องเป็นของ user",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"messages": [{"role": "user", "content": "RAG คืออะไร และต่างจาก fine-tune อย่างไร"}]}
            ]
        }
    }


class ChatResponse(BaseModel):
    answer: ResearchAnswer
    model: str