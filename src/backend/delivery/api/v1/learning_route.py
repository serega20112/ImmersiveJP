from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from src.backend.delivery.api.v1.helpers import resolve_return_to, track_href
from src.backend.dependencies.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
)
from src.backend.dependencies.service_dependencies import LearningServiceDependency
from src.backend.domain.content import TrackType
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash, render_template
from src.backend.services import LearningService
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
    learning_service: LearningServiceDependency,
):
    """Render the speech practice page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.

    Returns:
        The rendered speech practice template.
    """
    page = await learning_service.get_speech_practice_page(current_user.id)
    return await render_template(request, "learn/speech.html", page=page)


@learning_router.post("/speech", name="learning.speech_generate")
async def speech_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    words_text: Annotated[str, Form()],
):
    """Handle speech practice generation.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.
        words_text: The words to generate speech practice for.

    Returns:
        The rendered speech practice template or a redirect.
    """
    try:
        page = await learning_service.generate_speech_practice(
            current_user.id,
            words_text,
        )
        return await render_template(request, "learn/speech.html", page=page)
    except (InvalidSpeechWordsError, SpeechRateLimitExceededError) as error:
        flash(request, str(error), "error")
        return RedirectResponse(url="/learn/speech", status_code=status.HTTP_303_SEE_OTHER)


@learning_router.get("/language", name="learning.language")
async def language_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
):
    """Render the language learning track page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.

    Returns:
        The rendered track template.
    """
    return await _render_track_page(
        request,
        current_user,
        TrackType.LANGUAGE,
        learning_service,
    )


@learning_router.get("/culture", name="learning.culture")
async def culture_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
):
    """Render the culture learning track page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.

    Returns:
        The rendered track template.
    """
    return await _render_track_page(
        request,
        current_user,
        TrackType.CULTURE,
        learning_service,
    )


@learning_router.get("/history", name="learning.history")
async def history_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
):
    """Render the history learning track page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.

    Returns:
        The rendered track template.
    """
    return await _render_track_page(
        request,
        current_user,
        TrackType.HISTORY,
        learning_service,
    )


@learning_router.get("/{track}/cards/{card_id}", name="learning.card_page")
async def card_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: TrackType,
    card_id: int,
):
    """Render a specific card page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.
        track: The learning track type.
        card_id: ID of the card.

    Returns:
        The rendered card template or a redirect if not found.
    """
    try:
        page = await learning_service.get_card_page(
            current_user.id,
            track,
            card_id,
        )
        return await render_template(request, "learn/card.html", page=page)
    except CardNotFoundError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=status.HTTP_303_SEE_OTHER)


@learning_router.get("/{track}/work/{batch_number}", name="learning.work_page")
async def work_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: TrackType,
    batch_number: int,
):
    """Render the work page for a specific batch.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.
        track: The learning track type.
        batch_number: The batch number.

    Returns:
        The rendered work template.
    """
    try:
        page = await learning_service.get_track_work_page(
            current_user.id,
            track,
            batch_number,
        )
        return await render_template(request, "learn/work.html", page=page)
    except TrackWorkUnavailableError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=status.HTTP_303_SEE_OTHER)


@learning_router.post("/{track}/work/{batch_number}", name="learning.work_submit")
async def work_submit(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: TrackType,
    batch_number: int,
):
    """Handle track work submission.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        learning_service: The learning service dependency.
        track: The learning track type.
        batch_number: The batch number.

    Returns:
        The rendered work template with results or a redirect.
    """
    form = await request.form()
    answers = {
        key.removeprefix("answer_"): str(value)
        for key, value in form.items()
        if key.startswith("answer_")
    }
    try:
        page = await learning_service.submit_track_work(
            current_user.id,
            track,
            batch_number,
            answers,
        )
        return await render_template(request, "learn/work.html", page=page)
    except InvalidTrackWorkSubmissionError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=request.url.path, status_code=status.HTTP_303_SEE_OTHER)
    except TrackWorkUnavailableError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track.value), status_code=status.HTTP_303_SEE_OTHER)


@learning_router.post("/complete", name="learning.complete_card")
async def complete_card(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    card_id: Annotated[int, Form()],
    track: Annotated[str, Form()],
    return_to: Annotated[str | None, Form()] = None,
):
    """Handle card completion.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        learning_service: The learning service dependency.
        card_id: ID of the card to complete.
        track: The track key.
        return_to: Optional return URL.

    Returns:
        A redirect response.
    """
    try:
        await learning_service.complete_card(current_user.id, card_id)
        flash(request, "Карточка отмечена как пройденная.", "success")
    except CardOwnershipError as error:
        flash(request, str(error), "error")
    return RedirectResponse(
        url=resolve_return_to(return_to, track_href(track)),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@learning_router.get("/next", name="learning.next_cards")
async def next_cards(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    track: Annotated[str, Query()],
):
    """Handle generating the next batch of cards.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        learning_service: The learning service dependency.
        track: The track key.

    Returns:
        A redirect response.
    """
    try:
        await learning_service.get_next_cards(current_user.id, TrackType(track))
        flash(request, "Следующая партия готова.", "success")
    except (CurrentBatchNotCompletedError, LlmRateLimitExceededError) as error:
        flash(request, str(error), "error")
    return RedirectResponse(url=track_href(track), status_code=status.HTTP_303_SEE_OTHER)


@learning_router.get("/download-pdf", name="learning.download_pdf")
async def download_pdf(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    track: Annotated[str, Query()],
):
    """Handle exporting cards to PDF.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        learning_service: The learning service dependency.
        track: The track key.

    Returns:
        A PDF file response or a redirect.
    """
    try:
        document = await learning_service.export_cards_to_pdf(
            current_user.id,
            TrackType(track),
        )
        headers = {"Content-Disposition": f'attachment; filename="{document.filename}"'}
        return Response(content=document.content, media_type=document.media_type, headers=headers)
    except NoCompletedCardsError as error:
        flash(request, str(error), "error")
        return RedirectResponse(url=track_href(track), status_code=status.HTTP_303_SEE_OTHER)


async def _render_track_page(
    request: Request,
    current_user: UserViewDTO,
    track: TrackType,
    learning_service: LearningService,
):
    """Render the track page for a given track.

    Args:
        request: The incoming request.
        current_user: The current user.
        track: The learning track type.
        learning_service: The learning service instance.

    Returns:
        The rendered track template.
    """
    page = await learning_service.get_track_page(current_user.id, track)
    return await render_template(request, "learn/track.html", page=page)
