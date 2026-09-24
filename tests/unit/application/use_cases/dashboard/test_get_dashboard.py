"""
Юнит-тесты use case GetDashboardUseCase.

Проверяется сборка дашборда пользователя: ошибка при отсутствии пользователя,
формирование секций по трекам из отчёта о прогрессе и выбор рекомендации
в зависимости от факта завершения онбординга.
"""

import pytest

from src.application.dto.profile import (
    ProgressReportDTO,
    TrackProgressDTO,
    TrustComponentDTO,
    TrustScoreDTO,
)
from src.application.use_cases.dashboard.get_dashboard import GetDashboardUseCase
from tests.fixtures.factories.user_factory import UserFactory


def _trust_score() -> TrustScoreDTO:
    """Собрать минимальную оценку прогресса для отчёта.

    Returns:
        TrustScoreDTO с одним компонентом.
    """
    return TrustScoreDTO(
        score=42,
        band_key="medium",
        band_title="Средний",
        summary="summary",
        note="note",
        components=[TrustComponentDTO(label="Карточки", score=10, note="10 карточек")],
    )


def _report(tracks: list[TrackProgressDTO], next_step: str = "Продолжай текущую партию") -> ProgressReportDTO:
    """Собрать отчёт о прогрессе с заданными треками.

    Args:
        tracks: Прогресс по трекам.
        next_step: Рекомендуемый следующий шаг.

    Returns:
        ProgressReportDTO для подмены результата build_progress_report.
    """
    return ProgressReportDTO(
        total_completed=3,
        total_generated=10,
        completion_rate=30.0,
        next_step=next_step,
        tracks=tracks,
        trust_score=_trust_score(),
        skill_assessment=None,
    )


def _track_progress(track: str = "language", title: str = "Язык") -> TrackProgressDTO:
    """Собрать прогресс одного трека.

    Args:
        track: Ключ трека.
        title: Название трека.

    Returns:
        TrackProgressDTO с фиксированными счётчиками.
    """
    return TrackProgressDTO(
        track=track,
        title=title,
        completed_cards=3,
        generated_cards=10,
        current_batch=2,
        completion_rate=30.0,
        completed_batches=1,
        work_ready_batch=1,
    )


class _StubProgressReport:
    """Подмена BuildProgressReportUseCase с предопределённым результатом."""

    def __init__(self, report: ProgressReportDTO) -> None:
        """Инициализировать заглушку отчётом.

        Args:
            report: Отчёт, возвращаемый методом execute.
        """
        self.report = report
        self.requested: list[int] = []

    async def execute(self, user_id: int) -> ProgressReportDTO:
        """Запомнить запрос и вернуть заданный отчёт.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Отчёт о прогрессе, переданный в конструктор.
        """
        self.requested.append(user_id)
        return self.report


class TestGetDashboardUseCase:
    """Группа тестов юзкейса сборки дашборда пользователя."""

    async def test_raises_when_user_not_found(self, fake_uow) -> None:
        """
        Тестируем: сборку дашборда для несуществующего пользователя.
        Отдаём: пустой репозиторий пользователей.
        Ожидаем: выброс ValueError.
        """
        use_case = GetDashboardUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report([])),
        )

        with pytest.raises(ValueError, match="Пользователь не найден"):
            await use_case.execute(user_id=1)

    async def test_builds_sections_with_subtitle_and_href(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: формирование секций дашборда из отчёта о прогрессе.
        Отдаём: пользователь с завершённым онбордингом; отчёт с треком "language".
        Ожидаем: одна секция с заголовком трека, тематическим подзаголовком
                 и ссылкой вида "/learn/language".
        """
        user = UserFactory().build(user_id=7, onboarding_completed=True)
        fake_user_repository._by_id[7] = user
        use_case = GetDashboardUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report([_track_progress()])),
        )

        dashboard = await use_case.execute(user_id=7)

        assert len(dashboard.sections) == 1
        section = dashboard.sections[0]
        assert section.track == "language"
        assert section.title == "Язык"
        assert section.subtitle == "Фразы, грамматика и примеры"
        assert section.href == "/learn/language"
        assert dashboard.trust_score.score == 42

    async def test_uses_report_next_step_when_onboarded(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: выбор рекомендации для прошедшего онбординг пользователя.
        Отдаём: пользователь с onboarding_completed=True; отчёт со своим next_step.
        Ожидаем: рекомендация равна next_step из отчёта.
        """
        user = UserFactory().build(user_id=7, onboarding_completed=True)
        fake_user_repository._by_id[7] = user
        use_case = GetDashboardUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report([], next_step="Закончи партию")),
        )

        dashboard = await use_case.execute(user_id=7)

        assert dashboard.recommendation == "Закончи партию"

    async def test_prompts_onboarding_when_not_completed(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: выбор рекомендации для пользователя без онбординга.
        Отдаём: пользователь с onboarding_completed=False.
        Ожидаем: рекомендация призывает сначала пройти онбординг.
        """
        user = UserFactory().build(user_id=7, onboarding_completed=False)
        fake_user_repository._by_id[7] = user
        use_case = GetDashboardUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report([], next_step="Закончи партию")),
        )

        dashboard = await use_case.execute(user_id=7)

        assert dashboard.recommendation.startswith("Сначала пройди онбординг")
        assert dashboard.user_display_name == str(user.display_name)
        assert dashboard.speech_practice_href == "/learn/speech"
