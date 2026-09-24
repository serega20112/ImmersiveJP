"""
Юнит-тесты DTO профиля, прогресса и учебного плана.

Проверяются: значения по умолчанию отчётов, вложенность оценок
прогресса (trust score) и структура страницы учебного плана.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.profile import (
    AIAdviceDTO,
    DashboardDTO,
    DashboardSectionDTO,
    LearningPlanPageDTO,
    PlanContentModeDTO,
    PlanDictionaryLinkDTO,
    PlanModuleDTO,
    PlanPaceDTO,
    PlanStageDTO,
    ProgressReportDTO,
    TrackProgressDTO,
    TrustComponentDTO,
    TrustScoreDTO,
)
from src.application.dto.skill import SkillAssessmentDTO


def _trust_score() -> TrustScoreDTO:
    """Собрать минимальную корректную оценку прогресса для вложенных DTO."""
    return TrustScoreDTO(
        score=70,
        band_key="steady",
        band_title="Уверенно",
        summary="Хороший темп",
        note="Продолжай",
        components=[TrustComponentDTO(label="Карточки", score=30, note="Норма")],
    )


class TestTrustScoreDTO:
    """Группа тестов DTO оценки прогресса."""

    def test_requires_components(self) -> None:
        """
        Тестируем: обязательность списка компонентов оценки.
        Отдаём: оценку без components.
        Ожидаем: ValidationError.
        """
        with pytest.raises(ValidationError):
            TrustScoreDTO(score=1, band_key="k", band_title="t", summary="s", note="n")

    def test_keeps_components(self) -> None:
        """
        Тестируем: сохранение списка компонентов оценки.
        Отдаём: оценку с одним компонентом.
        Ожидаем: компонент доступен по индексу.
        """
        assert _trust_score().components[0].label == "Карточки"


class TestProgressDTOs:
    """Группа тестов DTO прогресса по трекам и итогового отчёта."""

    def test_track_progress_work_ready_batch_defaults_to_none(self) -> None:
        """
        Тестируем: значение по умолчанию партии, готовой к работе.
        Отдаём: прогресс трека без work_ready_batch.
        Ожидаем: поле равно None.
        """
        progress = TrackProgressDTO(
            track="jlpt",
            title="JLPT",
            completed_cards=3,
            generated_cards=5,
            current_batch=1,
            completion_rate=0.6,
            completed_batches=0,
        )

        assert progress.work_ready_batch is None

    def test_report_skill_assessment_optional(self) -> None:
        """
        Тестируем: необязательность оценки навыков в отчёте.
        Отдаём: отчёт без skill_assessment.
        Ожидаем: поле равно None, остальные данные сохранены.
        """
        report = ProgressReportDTO(
            total_completed=3,
            total_generated=5,
            completion_rate=0.6,
            next_step="Дальше",
            tracks=[],
            trust_score=_trust_score(),
        )

        assert report.skill_assessment is None
        assert report.trust_score.score == 70


class TestDashboardDTOs:
    """Группа тестов DTO дашборда."""

    def test_section_work_ready_batch_defaults_to_none(self) -> None:
        """
        Тестируем: значение по умолчанию партии в секции дашборда.
        Отдаём: секцию без work_ready_batch.
        Ожидаем: поле равно None, href сохранён.
        """
        section = DashboardSectionDTO(
            track="jlpt",
            title="JLPT",
            subtitle="Подзаголовок",
            completed_cards=1,
            generated_cards=4,
            completion_rate=0.25,
            completed_batches=0,
            href="/learn/jlpt",
        )

        assert section.work_ready_batch is None
        assert section.href == "/learn/jlpt"

    def test_advice_keeps_focus_points(self) -> None:
        """
        Тестируем: DTO совета от ИИ.
        Отдаём: совет с пунктами фокуса.
        Ожидаем: пункты сохранены.
        """
        advice = AIAdviceDTO(headline="Фокус", summary="Резюме", focus_points=["грамматика"])

        assert advice.focus_points == ["грамматика"]

    def test_dashboard_skill_assessment_optional(self) -> None:
        """
        Тестируем: необязательность оценки навыков на дашборде.
        Отдаём: дашборд без skill_assessment.
        Ожидаем: поле None, обязательные части на месте.
        """
        dashboard = DashboardDTO(
            user_display_name="Ая",
            recommendation="Продолжай",
            sections=[],
            trust_score=_trust_score(),
            speech_practice_href="/speech",
        )

        assert dashboard.skill_assessment is None
        assert dashboard.speech_practice_href == "/speech"


class TestLearningPlanDTOs:
    """Группа тестов DTO страницы учебного плана."""

    def test_module_defaults_items_to_empty(self) -> None:
        """
        Тестируем: значение по умолчанию пунктов модуля.
        Отдаём: модуль без пунктов.
        Ожидаем: items — пустой список.
        """
        assert PlanModuleDTO(title="Модуль").items == []

    def test_stage_defaults_optional_parts(self) -> None:
        """
        Тестируем: значения по умолчанию необязательных частей этапа.
        Отдаём: этап без focus_note и modules.
        Ожидаем: focus_note None, modules пустой список.
        """
        stage = PlanStageDTO(
            index=1,
            title="Этап",
            timeframe="2 недели",
            summary="Описание",
            status="active",
            status_label="Текущий",
        )

        assert stage.focus_note is None
        assert stage.modules == []

    def test_content_mode_and_pace_defaults(self) -> None:
        """
        Тестируем: значения по умолчанию правил и рекомендаций.
        Отдаём: режим контента и темп без списков.
        Ожидаем: все списки пусты.
        """
        mode = PlanContentModeDTO(title="Режим", summary="s", next_shift_note="n")
        pace = PlanPaceDTO(title="Темп", summary="s", detail_note="n")

        assert mode.rules == []
        assert mode.dictionary_links == []
        assert pace.guidance == []

    def test_page_defaults_optional_notes_and_stages(self) -> None:
        """
        Тестируем: значения по умолчанию страницы плана.
        Отдаём: страницу без horizon_note, recovery_note и stages.
        Ожидаем: обе заметки None, этапы — пустой список.
        """
        page = LearningPlanPageDTO(
            title="План",
            subtitle="Подзаголовок",
            horizon_title="Горизонт",
            current_stage_title="Этап",
            current_stage_timeframe="2 недели",
            current_stage_summary="Описание",
            next_action="Действие",
            parallel_note="Заметка",
            content_mode=PlanContentModeDTO(title="Режим", summary="s", next_shift_note="n"),
            pace_mode=PlanPaceDTO(title="Темп", summary="s", detail_note="n"),
        )

        assert page.horizon_note is None
        assert page.recovery_note is None
        assert page.stages == []

    def test_dictionary_link_keeps_fields(self) -> None:
        """
        Тестируем: DTO справочной ссылки.
        Отдаём: ссылку с адресом и пояснением.
        Ожидаем: значения сохранены.
        """
        link = PlanDictionaryLinkDTO(label="Jisho", href="https://jisho.org", note="Словарь")

        assert link.href == "https://jisho.org"

    def test_report_accepts_skill_assessment(self) -> None:
        """
        Тестируем: совместимость оценки навыков с отчётом о прогрессе.
        Отдаём: оценку навыков в составе отчёта.
        Ожидаем: отчёт принимает модель без ошибок.
        """
        report = ProgressReportDTO(
            total_completed=0,
            total_generated=0,
            completion_rate=0.0,
            next_step="Старт",
            tracks=[],
            trust_score=_trust_score(),
            skill_assessment=SkillAssessmentDTO(score=5, summary="Новичок"),
        )

        assert report.skill_assessment is not None
        assert report.skill_assessment.estimated_level is None
