from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import JSONResponse

from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.request_scope import get_request_container
from src.backend.dependencies.service_dependencies import ProfileServiceDependency
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template
from src.backend.use_case.profile import InvalidMentorMessageError

mentor_router = APIRouter(prefix="/tutor")


@mentor_router.get("", name="mentor.page")
async def tutor_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    profile_service: ProfileServiceDependency,
):
    page = await profile_service.get_mentor_page(current_user.id)
    return await render_template(request, "profile/mentor.html", page=page)


@mentor_router.post("", name="mentor.send")
async def tutor_send(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    profile_service: ProfileServiceDependency,
    message: str = Form(),
):
    try:
        page = await profile_service.send_mentor_message(current_user.id, message)
        return await render_template(request, "profile/mentor.html", page=page)
    except InvalidMentorMessageError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "mentor.page")


@mentor_router.post("/voice-input", name="mentor.voice_input")
async def tutor_voice_input(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    audio: UploadFile = File(),
):
    stt_client = get_request_container().root.stt_client
    audio_data = await audio.read()
    text = await stt_client.transcribe(audio_data)
    return JSONResponse({"text": text})
