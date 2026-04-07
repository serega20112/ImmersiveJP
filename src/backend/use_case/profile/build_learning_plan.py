from __future__ import annotations

from src.backend.dto.profile_dto import (
    LearningPlanPageDTO,
    PlanContentModeDTO,
    PlanDictionaryLinkDTO,
    PlanModuleDTO,
    PlanPaceDTO,
    PlanStageDTO,
    ProgressReportDTO,
)
from src.backend.domain.user import StudyTimeline
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.profile.build_progress_report import (
    BuildProgressReportUseCase,
)


_ROADMAP = (
    {
        "index": 0,
        "title": "База",
        "timeframe": "0-1 месяц",
        "summary": "Сначала ставится фундамент чтения и распознавания базовых слогов. Без этого дальше идти бессмысленно: грамматика и речь будут разваливаться на каждом новом шаге.",
        "modules": (
            (
                "Хирагана",
                (
                    "символы",
                    "дакутэн и хандакутэн",
                    "сочетания вроде きゃ / しゃ",
                    "маленькое つ",
                ),
            ),
            (
                "Катакана",
                (
                    "символы",
                    "долгие гласные ー",
                    "удвоение ッ",
                    "иностранные сочетания вроде ファ / ティ",
                ),
            ),
            (
                "Чтение",
                (
                    "простые слова",
                    "чтение вслух",
                    "ритм коротких фраз",
                ),
            ),
        ),
    },
    {
        "index": 1,
        "title": "Базовая грамматика",
        "timeframe": "1-3 месяц",
        "summary": "Здесь собирается каркас предложения: тема, объект, отрицание, вопросы и базовые глагольные формы. Это этап, где язык перестает быть списком слов.",
        "modules": (
            (
                "Предложения",
                (
                    "A は B です",
                    "вопросы с か",
                    "отрицание じゃないです",
                ),
            ),
            (
                "Частицы",
                (
                    "は как тема",
                    "が как субъект",
                    "を как объект",
                    "に для времени и направления",
                    "の для принадлежности",
                ),
            ),
            (
                "Глаголы",
                (
                    "ます-форма",
                    "отрицание",
                    "прошедшее время",
                ),
            ),
            (
                "Словарь",
                (
                    "бытовой словарь до ~300 слов",
                    "частые существительные и глаголы",
                ),
            ),
        ),
    },
    {
        "index": 2,
        "title": "Начало речи",
        "timeframe": "3-6 месяц",
        "summary": "На этом этапе язык начинает работать в коротких сценах: просьба, магазин, знакомство, бытовой диалог. Важно не просто помнить форму, а быстро доставать ее в ситуации.",
        "modules": (
            (
                "Глаголы",
                (
                    "て-форма",
                    "просьбы через ください",
                    "разрешение через いいです",
                    "запрет через だめ",
                ),
            ),
            (
                "Прилагательные",
                (
                    "い-прилагательные",
                    "な-прилагательные",
                    "прошедшие и отрицательные формы",
                ),
            ),
            (
                "Простые диалоги",
                (
                    "знакомство",
                    "магазин",
                    "повседневные сцены",
                ),
            ),
            (
                "Словарь",
                (
                    "расширение до ~800 слов",
                    "частые бытовые конструкции",
                ),
            ),
        ),
    },
    {
        "index": 3,
        "title": "Кандзи",
        "timeframe": "параллельно с этапа 2",
        "summary": "Кандзи не должны ждать идеального момента. Как только базовая речь пошла, чтение и письмо постепенно подхватываются параллельной дорожкой.",
        "modules": (
            (
                "Базовые кандзи",
                (
                    "числа",
                    "время",
                    "частые базовые слова",
                ),
            ),
            (
                "Чтения",
                (
                    "онъёми",
                    "кунъёми",
                    "контекстный выбор чтения",
                ),
            ),
            (
                "Письмо",
                (
                    "порядок черт",
                    "ручная практика",
                    "распознавание в словах",
                ),
            ),
        ),
    },
    {
        "index": 4,
        "title": "Уверенный базис",
        "timeframe": "6-12 месяц",
        "summary": "Этап, где базовые формы связываются в устойчивую практику: слушание, чтение и грамматика начинают работать вместе, а не по отдельности.",
        "modules": (
            (
                "Грамматика",
                (
                    "ている",
                    "たい",
                    "つもり",
                    "ことができる",
                ),
            ),
            (
                "Слушание",
                (
                    "аниме с разбором",
                    "подкасты",
                    "повторение фраз вслух",
                ),
            ),
            (
                "Чтение",
                (
                    "простые тексты",
                    "короткие диалоги",
                    "привычка читать без ромадзи",
                ),
            ),
            (
                "Словарь",
                (
                    "расширение до ~1500 слов",
                    "бытовые и учебные темы",
                ),
            ),
        ),
    },
    {
        "index": 5,
        "title": "Средний уровень",
        "timeframe": "1-2 год",
        "summary": "Здесь уже строится речь без постоянной опоры на заготовки. Добавляются сложные формы, больше кандзи и настоящее погружение в живой материал.",
        "modules": (
            (
                "Кандзи",
                (
                    "~1000 знаков",
                    "чтение в реальном контексте",
                ),
            ),
            (
                "Грамматика",
                (
                    "условные формы なら / たら",
                    "пассив",
                    "каузатив",
                    "сложные конструкции",
                ),
            ),
            (
                "Разговор",
                (
                    "свободные диалоги",
                    "выражение мыслей",
                    "ответы без долгой паузы",
                ),
            ),
            (
                "Погружение",
                (
                    "аниме без сабов",
                    "манга",
                    "игры",
                ),
            ),
        ),
    },
    {
        "index": 6,
        "title": "Продвинутый",
        "timeframe": "2-3 год",
        "summary": "На этом уровне язык уже используется как инструмент: для разговора, понимания длинных форматов, письма и переключения между стилями.",
        "modules": (
            (
                "Кандзи",
                (
                    "~2000+ знаков",
                    "быстрое чтение без постоянной расшифровки",
                ),
            ),
            (
                "Речь",
                (
                    "беглая разговорная речь",
                    "сленг",
                    "переключение между стилями",
                ),
            ),
            (
                "Понимание",
                (
                    "фильмы",
                    "интервью",
                    "живое общение",
                ),
            ),
            (
                "Письмо",
                (
                    "тексты",
                    "сообщения",
                    "практическая переписка",
                ),
            ),
        ),
    },
    {
        "index": 7,
        "title": "Финал",
        "timeframe": "после 3 лет и дальше",
        "summary": "Финальный этап не про очередной набор тем, а про устойчивую жизнь в языке: понимание без перевода, свободная речь и самостоятельное расширение словаря.",
        "modules": (
            (
                "Свобода использования",
                (
                    "свободный разговор",
                    "понимание без постоянного перевода",
                    "жизнь в языковой среде",
                ),
            ),
        ),
    },
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
        user_repository: AbstractUserRepository,
        build_progress_report_use_case: BuildProgressReportUseCase,
    ):
        self._user_repository = user_repository
        self._build_progress_report_use_case = build_progress_report_use_case

    async def execute(self, user_id: int) -> LearningPlanPageDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        report = await self._build_progress_report_use_case.execute(user_id)
        weak_points = list(report.skill_assessment.weak_points) if report.skill_assessment else []

        progress_stage_index = _stage_from_progress(report)
        weak_stage_index = _stage_from_weak_points(weak_points)
        current_stage_index = progress_stage_index
        recovery_note = None
        if weak_stage_index is not None and weak_stage_index < progress_stage_index:
            current_stage_index = weak_stage_index
            recovery_note = _recovery_note(weak_points, _ROADMAP[weak_stage_index]["title"])

        current_stage = _ROADMAP[current_stage_index]
        content_mode = _build_content_mode(current_stage_index, report.trust_score.score)
        pace_mode = _build_pace_mode(user.study_timeline)

        return LearningPlanPageDTO(
            title="Учебный план",
            subtitle=_subtitle_for_plan(current_stage_index, recovery_note is not None),
            current_stage_title=current_stage["title"],
            current_stage_timeframe=current_stage["timeframe"],
            current_stage_summary=current_stage["summary"],
            recovery_note=recovery_note,
            next_action=_next_action(report, weak_points, current_stage["title"]),
            parallel_note="Культура и история идут рядом с языком: они не заменяют языковую дорожку, а дают сцены, контекст и повторение в новых ситуациях.",
            content_mode=content_mode,
            pace_mode=pace_mode,
            stages=_build_stage_dtos(
                current_stage_index=current_stage_index,
                progress_stage_index=progress_stage_index,
                weak_stage_index=weak_stage_index,
            ),
        )


def _stage_from_progress(report: ProgressReportDTO) -> int:
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
    stage_map = (
        (0, {"Хирагана", "Катакана", "Чтение слов"}),
        (1, {"Частицы", "Базовый порядок предложения", "Отрицательная форма"}),
        (2, {"Базовая лексика", "Формулы вежливости", "Вежливая просьба", "Бытовые сцены"}),
        (4, {"Намерение и план", "Связность фразы", "Точность в контексте"}),
        (5, {"Регистр речи", "Чтение канжи в контексте"}),
    )

    weak_set = set(weak_points)
    for stage_index, labels in stage_map:
        if weak_set & labels:
            return stage_index
    return None


def _recovery_note(weak_points: list[str], stage_title: str) -> str:
    visible = ", ".join(weak_points[:3])
    return (
        f"Сейчас план не толкает тебя дальше по новой сложности. Сначала нужно выровнять блок '{stage_title}'. "
        f"Главные просадки: {visible}."
    )


def _subtitle_for_plan(current_stage_index: int, recovery_mode: bool) -> str:
    if recovery_mode:
        return "План временно возвращает фокус к базе, пока слабые места не перестанут ломать следующие этапы."
    if current_stage_index <= 1:
        return "Сначала собирается фундамент: чтение, базовые формы и устойчивый каркас предложения."
    if current_stage_index <= 4:
        return "Сейчас задача не просто знать формы, а использовать их в сценах, диалогах и чтении."
    return "План смещается в сторону погружения: меньше опоры на перевод и больше самостоятельной работы с японским."


def _next_action(
    report: ProgressReportDTO,
    weak_points: list[str],
    current_stage_title: str,
) -> str:
    if weak_points:
        return (
            f"Ближайший фокус: закрыть слабые зоны в блоке '{current_stage_title}' и только потом расширять новый материал. "
            f"После этого возвращайся к текущей партии и контрольной работе."
        )
    return report.next_step


def _build_content_mode(current_stage_index: int, trust_score: int) -> PlanContentModeDTO:
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
            dictionary_links=[
                PlanDictionaryLinkDTO(**item) for item in _DICTIONARY_LINKS[:2]
            ],
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


def _build_stage_dtos(
    *,
    current_stage_index: int,
    progress_stage_index: int,
    weak_stage_index: int | None,
) -> list[PlanStageDTO]:
    stages: list[PlanStageDTO] = []
    for stage in _ROADMAP:
        index = stage["index"]
        status, status_label = _status_for_stage(index, current_stage_index)
        focus_note = None
        if weak_stage_index is not None and index == weak_stage_index and weak_stage_index < progress_stage_index:
            focus_note = "Пока здесь есть просадка, план удерживает фокус на повторении базы."
        elif index == 3 and current_stage_index >= 2:
            focus_note = "Кандзи идут параллельной дорожкой и не ждут, пока вся речь станет идеальной."

        stages.append(
            PlanStageDTO(
                index=index,
                title=stage["title"],
                timeframe=stage["timeframe"],
                summary=stage["summary"],
                status=status,
                status_label=status_label,
                focus_note=focus_note,
                modules=[
                    PlanModuleDTO(title=module_title, items=list(items))
                    for module_title, items in stage["modules"]
                ],
            )
        )
    return stages


def _status_for_stage(index: int, current_stage_index: int) -> tuple[str, str]:
    if index < current_stage_index:
        return "done", "опора уже должна держаться"
    if index == current_stage_index:
        return "current", "текущий фокус"
    if index == current_stage_index + 1:
        return "next", "следом"
    return "upcoming", "дальше по плану"
