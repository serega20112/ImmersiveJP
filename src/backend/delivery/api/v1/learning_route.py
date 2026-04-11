from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi.responses import RedirectResponse

from src.backend.dependencies.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
)
from src.backend.delivery.api.v1.helpers import get_learning_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.delivery.api.v1.helpers import resolve_return_to
from src.backend.delivery.api.v1.helpers import track_href
from src.backend.domain.content import TrackType
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template
from src.backend.use_case.learning.complete_card import CardOwnershipError
from src.backend.use_case.learning.export_cards_to_pdf import NoCompletedCardsError
from src.backend.use_case.learning.generate_cards import LlmRateLimitExceededError
from src.backend.use_case.learning.generate_speech_practice import (
    InvalidSpeechWordsError,
    SpeechRateLimitExceededError,
)
from src.backend.use_case.learning.get_card_page import CardNotFoundError
from src.backend.use_case.learning.get_next_cards import CurrentBatchNotCompletedError
from src.backend.use_case.learning.get_track_work_page import TrackWorkUnavailableError
from src.backend.use_case.learning.submit_track_work import (
    InvalidTrackWorkSubmissionError,
)

learning_router = APIRouter(prefix="/learn")


@learning_router.get("/speech", name="learning.speech_page")
async def speech_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
):
    page = await get_learning_service(request).get_speech_practice_page(current_user.id)
    return render_template(request, "learn/speech.html", page=page)


@learning_router.post("/speech", name="learning.speech_generate")
async def speech_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    words_text: Annotated[str, Form()],
):
    try:
        page = await get_learning_service(request).generate_speech_practice(
            current_user.id,
            words_text,
        )
        return render_template(request, "learn/speech.html", page=page)
    except (InvalidSpeechWordsError, SpeechRateLimitExceededError) as error:
        flash(request, str(error), "error")
        return RedirectResponse(url="/learn/speech", status_code=303)


@learning_router.get("/language", name="learning.language")
async def language_track(request: Request):
    return await _render_track_page(request, TrackType.LANGUAGE)


@learning_router.get("/culture", name="learning.culture")
async def culture_track(request: Request):
    return await _render_track_page(request, TrackType.CULTURE)


@learning_router.get("/history", name="learning.history")
async def history_track(request: Request):
    return await _render_track_page(request, TrackType.HISTORY)


@learning_router.get("/{track}/cards/{card_id}", name="learning.card_page")
async def card_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    track: TrackType,
    card_id: int,
):
    try:
        page = await get_learning_service(request).get_card_page(
            current_user.id,
            track,
            card_id,
        )
        return render_template(request, "learn/card.html", page=page)
    except CardNotFoundError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=303)


@learning_router.get("/{track}/work/{batch_number}", name="learning.work_page")
async def work_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    track: TrackType,
    batch_number: int,
):
    try:
        page = await get_learning_service(request).get_track_work_page(
            current_user.id,
            track,
            batch_number,
        )
        return render_template(request, "learn/work.html", page=page)
    except TrackWorkUnavailableError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=303)


@learning_router.post("/{track}/work/{batch_number}", name="learning.work_submit")
async def work_submit(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    track: TrackType,
    batch_number: int,
):
    form = await request.form()
    answers = {
        key.removeprefix("answer_"): str(value)
        for key, value in form.items()
        if key.startswith("answer_")
    }
    try:
        page = await get_learning_service(request).submit_track_work(
            current_user.id,
            track,
            batch_number,
            answers,
        )
        return render_template(request, "learn/work.html", page=page)
    except InvalidTrackWorkSubmissionError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=request.url.path, status_code=303)
    except TrackWorkUnavailableError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=303)


@learning_router.post("/complete", name="learning.complete_card")
async def complete_card(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    card_id: Annotated[int, Form()],
    track: Annotated[str, Form()],
    return_to: Annotated[str | None, Form()] = None,
):
    try:
        await get_learning_service(request).complete_card(current_user.id, card_id)
        flash(request, "Карточка отмечена как пройденная.", "success")
    except CardOwnershipError as error:
        flash(request, str(error), "error")
    return RedirectResponse(
        url=resolve_return_to(return_to, track_href(track)),
        status_code=303,
    )


@learning_router.get("/next", name="learning.next_cards")
async def next_cards(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    track: Annotated[str, Query()],
):
    try:
        await get_learning_service(request).get_next_cards(
            current_user.id, TrackType(track)
        )
        flash(request, "Следующая партия готова.", "success")
    except (CurrentBatchNotCompletedError, LlmRateLimitExceededError) as error:
        flash(request, str(error), "error")
    return RedirectResponse(url=track_href(track), status_code=303)


@learning_router.get("/download-pdf", name="learning.download_pdf")
async def download_pdf(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    track: Annotated[str, Query()],
):
    try:
        document = await get_learning_service(request).export_cards_to_pdf(
            current_user.id,
            TrackType(track),
        )
        headers = {"Content-Disposition": f'attachment; filename="{document.filename}"'}
        return Response(
            content=document.content, media_type=document.media_type, headers=headers
        )
    except NoCompletedCardsError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track), status_code=303)


async def _render_track_page(request: Request, track: TrackType):
    current_user = await require_onboarded_user(request)
    page = await get_learning_service(request).get_track_page(current_user.id, track)
    return render_template(request, "learn/track.html", page=page)
