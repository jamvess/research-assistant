from fastapi import FastAPI

from app.errors import register_error_handlers
from app.routers import chat, health

app = FastAPI(
    title="Research Assistant API",
    description="ผู้ช่วยวิจัยที่ตอบคำถามแบบมีโครงสร้าง ขับเคลื่อนด้วย LLM บน Groq",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(chat.router)
register_error_handlers(app)