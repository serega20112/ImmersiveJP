from __future__ import annotations

from src.application.dto.profile import (
    LearningPlanPageDTO,
    PlanContentModeDTO,
    PlanDictionaryLinkDTO,
    PlanModuleDTO,
    PlanPaceDTO,
    PlanStageDTO,
    ProgressReportDTO,
)
from src.application.exceptions import CourseProgramUnavailableError
from src.application.interfaces import UnitOfWork
from src.application.use_cases.profile.build_progress_report import (
    BuildProgressReportUseCase,
)
from src.domain.entities.course import CourseStage
from src.domain.value_objects.user import StudyTimeline

_KANJI_STAGE_CODE = "kanji"

_WEAK_POINT_STAGES: tuple[tuple[int, frozenset[str]], ...] = (
    (0, frozenset({"Хирагана", "Катакана", "Чтение слов"})),
    (1, frozenset({"Частицы", "Базовый порядок предложения", "Отрицательная форма"})),
    (
        2,
        frozenset(
            {
                "Базовая лексика",
                "Формулы вежливости",
                "Вежливая просьба",
                "Бытовые сцены",
            }
        ),
    ),
    (4, frozenset({"Намерение и план", "Связность фразы", "Точность в контексте"})),
    (5, frozenset({"Регистр речи", "Чтение канжи в контексте"})),
)


_DICTIONARY_LINKS = (
    {
        "label": "Jisho",
        "href": "https://jisho.org/",
        "note": "Быстрый словарь по словам, формам и кандзи.",
    },
    {
        "label": "Takoboto",
        "href": "https://takoboto.jp/",
        "note": "Удобный разбор слов, кандзи и примеров.",
    },
    {
        "label": "Weblio",
        "href": "https://www.weblio.jp/",
        "note": "Полезен, когда нужно посмотреть значение в японском объяснении.",
    },
)


class BuildLearningPlanUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        build_progress_report_use_case: BuildProgressReportUseCase,
    ):
        """Initialize the build learning plan use case.

        Args:
            uow: Unit of work for database transactions.
            build_progress_report_use_case: Use case for building progress reports.
        """
        self._uow = uow
        self._build_progress_report_use_case = build_progress_report_use_case

    async def execute(self, user_id: int) -> LearningPlanPageDTO:
        """Собрать учебный план пользователя.

        Этапы программы читаются из справочных таблиц, поэтому порядок и
        содержимое блока можно менять миграцией, не трогая код.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Данные страницы учебного плана.

        Raises:
            ValueError: Если пользователь не найден.
            CourseProgramUnavailableError: Если программа не заполнена.
        """
        async with self._uow as uow:
            user_repository = uow.users
            course_repository = uow.course
            user = await user_repository.get_by_id(user_id)
            stages = await course_repository.list_stages()
        if user is None:
            raise ValueError("Пользователь не найден")
        if not stages:
            raise CourseProgramUnavailableError(
                "Учебная программа пуста: не применена миграция course_stages"
            )

        report = await self._build_progress_report_use_case.execute(user_id)
        weak_points = list(report.skill_assessment.weak_points) if report.skill_assessment else []

        stages_by_position = {stage.position: stage for stage in stages}
        progress_stage_index = _stage_from_progress(report)
        weak_stage_index = _stage_from_weak_points(weak_points)
        current_stage_index = progress_stage_index
        recovery_note = None
        if weak_stage_index is not None and weak_stage_index < progress_stage_index:
            current_stage_index = weak_stage_index
            recovery_note = _recovery_note(
                weak_points,
                _select_stage(stages_by_position, weak_stage_index).title,
            )

        current_stage = _select_stage(stages_by_position, current_stage_index)
        content_mode = _build_content_mode(current_stage_index, report.trust_score.score)
        pace_mode = _build_pace_mode(user.study_timeline)
        horizon_stage_index = max(
            current_stage_index,
            _timeline_horizon_index(user.study_timeline),
        )
        horizon_stage = _select_stage(stages_by_position, horizon_stage_index)

        return LearningPlanPageDTO(
            title="Учебный план",
            subtitle=_subtitle_for_plan(current_stage_index, recovery_note is not None),
            horizon_title=(f"Горизонт на текущий срок: до этапа '{horizon_stage.title}'"),
            horizon_note=_horizon_note(
                study_timeline=user.study_timeline,
                horizon_stage=horizon_stage,
            ),
            current_stage_title=current_stage.title,
            current_stage_timeframe=current_stage.timeframe,
            current_stage_summary=current_stage.summary,
            recovery_note=recovery_note,
            next_action=_next_action(report, weak_points, current_stage.title),
            parallel_note="Культура и история идут рядом с языком: они не заменяют языковую дорожку, а дают сцены, контекст и повторение в новых ситуациях.",
            content_mode=content_mode,
            pace_mode=pace_mode,
            stages=_build_stage_dtos(
                program=stages,
                current_stage_index=current_stage_index,
                progress_stage_index=progress_stage_index,
                weak_stage_index=weak_stage_index,
                visible_horizon_index=horizon_stage_index,
            ),
        )


def _select_stage(stages_by_position: dict[int, CourseStage], position: int) -> CourseStage:
    """Достать этап по порядковому номеру из загруженной программы.

    Номера этапов приходят из расчётов прогресса и срока, поэтому пропущенный
    номер означает рассогласование данных программы с кодом, и молча подменять
    его соседним этапом нельзя.

    Args:
        stages_by_position: Этапы, индексированные позицией.
        position: Нужная позиция этапа.

    Returns:
        Найденный этап.

    Raises:
        CourseProgramUnavailableError: Если этапа с такой позицией нет.
    """
    stage = stages_by_position.get(position)
    if stage is None:
        raise CourseProgramUnavailableError(f"В учебной программе нет этапа с номером {position}")
    return stage


def _stage_from_progress(report: ProgressReportDTO) -> int:
    """Determine the learning stage index from progress data.

    Args:
        report: The progress report.

    Returns:
        The stage index (0-7).
    """
    score = report.trust_score.score
    total_completed = report.total_completed

    if report.total_generated == 0 or total_completed < 10 or score < 25:
        return 0
    if score < 40:
        return 1
    if score < 55:
        return 2
    if score < 65:
        return 3
    if score < 75:
        return 4
    if score < 88:
        return 5
    if score < 96:
        return 6
    return 7


def _stage_from_weak_points(weak_points: list[str]) -> int | None:
    """Determine the stage index from weak points.

    Args:
        weak_points: List of weak point labels.

    Returns:
        The stage index, or None if no weak points match.
    """
    weak_set = set(weak_points)
    for stage_index, labels in _WEAK_POINT_STAGES:
        if weak_set & labels:
            return stage_index
    return None


def _recovery_note(weak_points: list[str], stage_title: str) -> str:
    """Build a recovery note for weak points at a stage.

    Args:
        weak_points: List of weak point labels.
        stage_title: The title of the stage to recover.

    Returns:
        The recovery note text.
    """
    visible = ", ".join(weak_points[:3])
    return (
        f"Сейчас план не толкает тебя дальше по новой сложности. Сначала нужно выровнять блок '{stage_title}'. "
        f"Главные просадки: {visible}."
    )


def _subtitle_for_plan(current_stage_index: int, recovery_mode: bool) -> str:
    """Build a subtitle for the learning plan page.

    Args:
        current_stage_index: The current stage index.
        recovery_mode: Whether recovery mode is active.

    Returns:
        The subtitle text.
    """
    if recovery_mode:
        return "План временно возвращает фокус к базе, пока слабые места не перестанут ломать следующие этапы."
    if current_stage_index <= 1:
        return (
            "Сначала собирается фундамент: чтение, базовые формы и устойчивый каркас предложения."
        )
    if current_stage_index <= 4:
        return "Сейчас задача не просто знать формы, а использовать их в сценах, диалогах и чтении."
    return "План смещается в сторону погружения: меньше опоры на перевод и больше самостоятельной работы с японским."


def _next_action(
    report: ProgressReportDTO,
    weak_points: list[str],
    current_stage_title: str,
) -> str:
    """Build the next action recommendation.

    Args:
        report: The progress report.
        weak_points: List of weak point labels.
        current_stage_title: The title of the current stage.

    Returns:
        The next action text.
    """
    if weak_points:
        return (
            f"Ближайший фокус: закрыть слабые зоны в блоке '{current_stage_title}' и только потом расширять новый материал. "
            f"После этого возвращайся к текущей партии и контрольной работе."
        )
    return report.next_step


def _build_content_mode(current_stage_index: int, trust_score: int) -> PlanContentModeDTO:
    """Build the content mode configuration.

    Args:
        current_stage_index: The current stage index.
        trust_score: The user's trust score.

    Returns:
        The content mode DTO.
    """
    if current_stage_index <= 1 or trust_score < 40:
        return PlanContentModeDTO(
            title="Японский с полной опорой",
            summary="Материал подается так, чтобы чтение не ломалось: японский текст идет в простом виде, рядом есть ромадзи и перевод, а ключевые слова закрепляются парами.",
            next_shift_note="Следующий переход: убрать зависимость от ромадзи после того, как чтение и базовые формы держатся без постоянных ошибок.",
            rules=[
                "основной текст без тяжелого перегруза кандзи",
                "ромадзи показаны рядом с фразой",
                "перевод виден сразу",
                "ключевые слова закрепляются как слово -> перевод",
            ],
        )
    if current_stage_index <= 4 or trust_score < 78:
        return PlanContentModeDTO(
            title="Японский без ромадзи",
            summary="Ромадзи убираются из основной подачи. Пользователь читает японский текст напрямую, но перевод и опорные ключевые слова еще остаются на экране.",
            next_shift_note="Следующий переход: оставить только японский текст и искать незнакомые слова уже через словарь, а не через готовый перевод.",
            rules=[
                "основной текст показывается на японском",
                "ромадзи не являются основной опорой",
                "перевод остается рядом для проверки понимания",
                "ключевые слова идут как японский термин -> русский смысл",
            ],
            dictionary_links=[PlanDictionaryLinkDTO(**item) for item in _DICTIONARY_LINKS[:2]],
        )
    return PlanContentModeDTO(
        title="Почти чистое погружение",
        summary="Материал смещается в японский по умолчанию. Перевод больше не подается как костыль: незнакомые слова ищутся через словари, а понимание собирается из контекста.",
        next_shift_note="Дальше режим держится на японском тексте, а словари становятся рабочим инструментом вместо постоянного перевода.",
        rules=[
            "карточки и задания идут в первую очередь на японском",
            "перевод не показывается автоматически",
            "новые слова ищутся через внешние словари",
            "повторение строится через чтение, речь и реальные сцены",
        ],
        dictionary_links=[PlanDictionaryLinkDTO(**item) for item in _DICTIONARY_LINKS],
    )


def _build_pace_mode(study_timeline: StudyTimeline | None) -> PlanPaceDTO:
    """Build the pace mode configuration based on study timeline.

    Args:
        study_timeline: The user's study timeline, or None.

    Returns:
        The pace mode DTO.
    """
    timeline = study_timeline or StudyTimeline.FLEXIBLE

    if timeline == StudyTimeline.THREE_MONTHS:
        return PlanPaceDTO(
            title="Срок: 3 месяца",
            summary="Режим сжатый. Система будет держать фокус на самом частом и прикладном материале, а длинные обходные объяснения отрежет.",
            detail_note="Карточки и работы будут плотнее: меньше теории ради теории, быстрее возврат к слабым местам и раньше проверка на практике.",
            guidance=[
                "приоритет у чтения, базовой грамматики и бытовой речи",
                "ромадзи и перевод будут убираться быстрее, если база держится",
                "новые темы чаще будут проходить через короткие контрольные работы",
            ],
        )
    if timeline == StudyTimeline.SIX_MONTHS:
        return PlanPaceDTO(
            title="Срок: 6 месяцев",
            summary="Режим интенсивный. Материал идет быстро, но еще остается место на пояснение сцены, паттерна и типичных ошибок.",
            detail_note="Система будет объяснять по делу: не сухо, но и без длинных лекций. Проверка прогресса будет идти чаще, чем в спокойном темпе.",
            guidance=[
                "новая грамматика сразу закрепляется в диалоге и задаче",
                "долги по партиям сильнее тормозят следующий материал",
                "контекст и повторение важнее красивой теории",
            ],
        )
    if timeline == StudyTimeline.ONE_YEAR:
        return PlanPaceDTO(
            title="Срок: 1 год",
            summary="Режим сбалансированный. Можно объяснять подробнее, не жертвуя темпом и не превращая каждую карточку в длинную лекцию.",
            detail_note="Это нормальный рабочий горизонт: система держит и базу, и речь, и постепенно уводит от опоры на ромадзи.",
            guidance=[
                "объяснения остаются подробными, но прикладными",
                "работы идут после закрытых партий и фиксируют, что материал реально держится",
                "культура и история подключаются как дополнительный контекст, а не как шум",
            ],
        )
    if timeline == StudyTimeline.TWO_YEARS:
        return PlanPaceDTO(
            title="Срок: 2 года и дольше",
            summary="Режим глубокий. Можно идти спокойнее и объяснять материал шире: с контекстом, связями между темами и более плавным ростом сложности.",
            detail_note="Система будет чаще оставлять пространство на чтение, повторение и постепенный отказ от перевода без спешки ради календаря.",
            guidance=[
                "больше внимания к чтению, кандзи и культурному контексту",
                "сложность повышается мягче, но требования к устойчивости знаний не падают",
                "старые темы будут чаще возвращаться в новом контексте",
            ],
        )
    return PlanPaceDTO(
        title="Срок: без жесткого дедлайна",
        summary="Режим гибкий. Система подстраивает темп под реальное качество ответа и закрытые партии, а не под заранее зафиксированный календарь.",
        detail_note="Если база держится слабо, план спокойно возвращает тебя назад. Если материал идет стабильно, плотность и уровень повышаются быстрее.",
        guidance=[
            "темп зависит от trust score и слабых мест, а не от формальной даты",
            "объяснения остаются подробными там, где реально есть просадка",
            "контрольные работы используются как точка решения: можно идти дальше или рано",
        ],
    )


def _timeline_horizon_index(study_timeline: StudyTimeline | None) -> int:
    """Get the horizon stage index for a study timeline.

    Args:
        study_timeline: The user's study timeline, or None.

    Returns:
        The horizon stage index.
    """
    timeline = study_timeline or StudyTimeline.FLEXIBLE
    horizon_map = {
        StudyTimeline.THREE_MONTHS: 1,
        StudyTimeline.SIX_MONTHS: 3,
        StudyTimeline.ONE_YEAR: 4,
        StudyTimeline.TWO_YEARS: 5,
        StudyTimeline.FLEXIBLE: 7,
    }
    return horizon_map[timeline]


def _horizon_note(
    *,
    study_timeline: StudyTimeline | None,
    horizon_stage: CourseStage,
) -> str | None:
    """Build a horizon note for the learning plan.

    Args:
        study_timeline: The user's study timeline.
        horizon_stage: The stage closing the visible horizon.

    Returns:
        The horizon note text, or None for flexible timelines.
    """
    timeline = study_timeline or StudyTimeline.FLEXIBLE
    if timeline == StudyTimeline.FLEXIBLE:
        return None

    return (
        f"Дальние этапы за пределами срока сейчас скрыты. В этом режиме план держит "
        f"фокус до блока '{horizon_stage.title}', а не размазывает внимание до финала."
    )


def _build_stage_dtos(
    *,
    program: list[CourseStage],
    current_stage_index: int,
    progress_stage_index: int,
    weak_stage_index: int | None,
    visible_horizon_index: int,
) -> list[PlanStageDTO]:
    """Собрать DTO видимых этапов учебного плана.

    Args:
        program: Этапы загруженной программы.
        current_stage_index: Позиция текущего этапа.
        progress_stage_index: Позиция этапа, до которого дошёл прогресс.
        weak_stage_index: Позиция этапа со слабой базой, либо None.
        visible_horizon_index: Максимальная видимая позиция этапа.

    Returns:
        Список этапов, не выходящих за горизонт срока.
    """
    rows: list[PlanStageDTO] = []
    for stage in program:
        index = stage.position
        if index > visible_horizon_index:
            continue
        status, status_label = _status_for_stage(index, current_stage_index)
        focus_note = None
        if (
            weak_stage_index is not None
            and index == weak_stage_index
            and weak_stage_index < progress_stage_index
        ):
            focus_note = "Пока здесь есть просадка, план удерживает фокус на повторении базы."
        elif stage.code == _KANJI_STAGE_CODE and current_stage_index >= 2:
            focus_note = (
                "Кандзи идут параллельной дорожкой и не ждут, пока вся речь станет идеальной."
            )

        rows.append(
            PlanStageDTO(
                index=index,
                title=stage.title,
                timeframe=stage.timeframe,
                summary=stage.summary,
                status=status,
                status_label=status_label,
                focus_note=focus_note,
                modules=[
                    PlanModuleDTO(
                        title=module.title, items=[topic.title for topic in module.topics]
                    )
                    for module in stage.modules
                ],
            )
        )
    return rows


def _status_for_stage(index: int, current_stage_index: int) -> tuple[str, str]:
    """Determine the status label for a stage.

    Args:
        index: The stage index.
        current_stage_index: The current stage index.

    Returns:
        A tuple of (status_key, status_label).
    """
    if index < current_stage_index:
        return "done", "опора уже должна держаться"
    if index == current_stage_index:
        return "current", "текущий фокус"
    if index == current_stage_index + 1:
        return "next", "следом"
    return "upcoming", "дальше по плану"
