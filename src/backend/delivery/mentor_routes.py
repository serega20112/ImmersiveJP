from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/mentor", tags=["mentor"])


@router.post(
    "/ask",
    status_code=status.HTTP_200_OK,
)
async def ask_mentor():
    return JSONResponse({"status": "mentor endpoint placeholder"})
