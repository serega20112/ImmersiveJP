from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import base64

from src.backend.dependencies.current_user import resolve_current_user
from src.backend.dependencies.database import get_db
from src.backend.infrastructure.external.embedding_client import EmbeddingClient
from src.backend.infrastructure.external.llm_client import LLMClient
from src.backend.infrastructure.external.tts_client import TTSClient
from src.backend.services.mentor_service import MentorService

router = APIRouter(prefix="/api/mentor", tags=["mentor"])

def get_mentor_service(
    embed_client: EmbeddingClient = Depends(),
    llm_client: LLMClient = Depends(),
    tts_client: TTSClient = Depends(),
    db: Session = Depends(get_db),
) -> MentorService:
    """Create MentorService with required dependencies."""
    return MentorService(embed_client, llm_client, tts_client)

@router.post("/ask")
async def ask_mentor(
    question: str,
    user=Depends(resolve_current_user),
    mentor: MentorService = Depends(get_mentor_service),
    db: Session = Depends(get_db),
):
    """Ask the AI‑tutor a question and receive a text and audio answer.

    Returns JSON with:
        - answer: generated text answer
        - audio: base64‑encoded MP3 audio of the answer
    """
    answer_text, audio_bytes = await mentor.answer(db, user.id, question)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return JSONResponse(content={"answer": answer_text, "audio": audio_b64})
