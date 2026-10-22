from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="เช็กว่าระบบยังทำงานอยู่")
async def health() -> dict[str, str]:
    return {"status": "ok"}