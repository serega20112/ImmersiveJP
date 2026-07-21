from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.service_dependencies import (
    ProfileServiceDependency,
    STTClientDependency,
)
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash, render_template
from src.backend.use_case.profile import InvalidMentorMessageError

mentor_router = APIRouter(prefix="/tutor")


@mentor_router.get("", name="mentor.page")
async def tutor_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    profile_service: ProfileServiceDependency,
):
    """Render the mentor/tutor page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        profile_service: The profile service dependency.

    Returns:
        The rendered mentor template.
    """
    page = await profile_service.get_mentor_page(current_user.id)
    return await render_template(request, "profile/mentor.html", page=page)


@mentor_router.post("", name="mentor.send")
async def tutor_send(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    profile_service: ProfileServiceDependency,
    message: str = Form(),
):
    """Handle sending a message to the tutor.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        profile_service: The profile service dependency.
        message: The message text.

    Returns:
        The rendered mentor template or a redirect.
    """
    try:
        page = await profile_service.send_mentor_message(current_user.id, message)
        return await render_template(request, "profile/mentor.html", page=page)
    except InvalidMentorMessageError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "mentor.page")


@mentor_router.post("/voice-input", name="mentor.voice_input")
async def tutor_voice_input(
    _request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    stt_client: STTClientDependency,
    audio: UploadFile = File(),  # noqa: B008
):
    """Handle voice input transcription.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        audio: The uploaded audio file.
        stt_client: The speech-to-text client dependency.

    Returns:
        A JSON response with the transcribed text.
    """
    audio_data = await audio.read()
    text = await stt_client.transcribe(audio_data)
    return JSONResponse({"text": text})
