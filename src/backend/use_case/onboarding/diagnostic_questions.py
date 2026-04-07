from __future__ import annotations

from src.backend.domain.user import LanguageLevel, SkillAssessment, StudyTimeline
from src.backend.dto.onboarding_dto import (
    DiagnosticOptionDTO,
    DiagnosticQuestionDTO,
    DiagnosticQuestionGroupDTO,
    StudyTimelineOptionDTO,
)


_DIAGNOSTIC_BANKS = {
    LanguageLevel.ZERO: {
        "title": "Стартовый срез",
        "description": "Проверяет, держится ли азбука, базовые слова и простые конструкции.",
        "questions": (
            {
                "key": "zero_reading_ka",
                "skill_label": "Хирагана",
                "prompt": "Как читается か?",
                "correct": "ka",
                "hints": (
                    "Это базовый слог на к.",
                    "Ответ начинается на 'ka'.",
                    "Правильное чтение: ka.",
                ),
                "options": (
                    ("ka", "ка", "Базовое чтение слога か."),
                    ("e", "э", "Это другой звук."),
                    ("ke", "кэ", "Слог близок, но не тот."),
                ),
            },
            {
                "key": "zero_word_mizu",
                "skill_label": "Базовая лексика",
                "prompt": "Что означает みず?",
                "correct": "water",
                "hints": (
                    "Это бытовое слово, не транспорт и не предмет мебели.",
                    "Речь про напиток.",
                    "Правильный ответ: вода.",
                ),
                "options": (
                    ("water", "вода", "Понимает бытовую лексику."),
                    ("train", "поезд", "Путает повседневные слова."),
                    ("window", "окно", "Пока не держит базовый словарь."),
                ),
            },
            {
                "key": "zero_polite_thanks",
                "skill_label": "Формулы вежливости",
                "prompt": "Какой вариант звучит как более вежливое 'спасибо'?",
                "correct": "arigatou_gozaimasu",
                "hints": (
                    "Ищи более длинную и формальную форму.",
                    "В ответе есть 'gozaimasu'.",
                    "Правильный ответ: ありがとうございます.",
                ),
                "options": (
                    (
                        "arigatou_gozaimasu",
                        "ありがとうございます",
                        "Более вежливая форма благодарности.",
                    ),
                    ("arigatou", "ありがとう", "Простая разговорная форма."),
                    ("ohayou", "おはよう", "Это приветствие."),
                ),
            },
            {
                "key": "zero_particle_direction",
                "skill_label": "Частицы",
                "prompt": "Какая частица показывает направление в 東京に行きます?",
                "correct": "ni",
                "hints": (
                    "Это частица точки назначения.",
                    "Правильная частица читается как 'ni'.",
                    "Ответ: に.",
                ),
                "options": (
                    ("ni", "に", "Частица направления и точки назначения."),
                    ("wa", "は", "Это тема, не направление."),
                    ("o", "を", "Это прямое дополнение."),
                ),
            },
            {
                "key": "zero_sentence_student",
                "skill_label": "Базовый порядок предложения",
                "prompt": "Какой вариант означает 'Я студент'?",
                "correct": "watashi_wa_gakusei_desu",
                "hints": (
                    "Ищи схему 'я + тема + студент + связка'.",
                    "Нужна частица 'wa'.",
                    "Правильный ответ: 私は学生です。",
                ),
                "options": (
                    (
                        "watashi_wa_gakusei_desu",
                        "私は学生です。",
                        "Верный базовый паттерн.",
                    ),
                    (
                        "watashi_o_gakusei_desu",
                        "私を学生です。",
                        "Частица выбрана неправильно.",
                    ),
                    (
                        "gakusei_ni_watashi_desu",
                        "学生に私です。",
                        "Порядок и частицы ломают смысл.",
                    ),
                ),
            },
        ),
    },
    LanguageLevel.BASIC: {
        "title": "Базовый срез",
        "description": "Проверяет чтение слов, простые формы и бытовые реплики.",
        "questions": (
            {
                "key": "basic_reading_kyou",
                "skill_label": "Чтение слов",
                "prompt": "Как читается 今日?",
                "correct": "kyou",
                "hints": (
                    "Слово означает 'сегодня'.",
                    "Чтение начинается на 'kyo'.",
                    "Правильный ответ: kyou.",
                ),
                "options": (
                    ("kyou", "きょう", "Нормальное чтение частого слова."),
                    ("imahi", "いまひ", "Это не словарное чтение."),
                    ("ashita", "あした", "Это 'завтра'."),
                ),
            },
            {
                "key": "basic_request",
                "skill_label": "Вежливая просьба",
                "prompt": "Какой вариант лучше подходит для вежливой просьбы 'пожалуйста, подождите'?",
                "correct": "chotto_matte_kudasai",
                "hints": (
                    "Нужна вежливая просьба, не простая команда.",
                    "Ищи форму с 'kudasai'.",
                    "Правильный ответ: ちょっと待ってください。",
                ),
                "options": (
                    (
                        "chotto_matte_kudasai",
                        "ちょっと待ってください。",
                        "Вежливая просьба.",
                    ),
                    ("matsu", "待つ。", "Это словарная форма, не просьба."),
                    ("matte", "待って。", "Это просто короткая команда."),
                ),
            },
            {
                "key": "basic_object_particle",
                "skill_label": "Частицы",
                "prompt": "Какая частица нужна в 水___飲みます?",
                "correct": "o",
                "hints": (
                    "Нужен маркер объекта действия.",
                    "Читается как 'o'.",
                    "Правильный ответ: を.",
                ),
                "options": (
                    ("o", "を", "Маркер прямого дополнения."),
                    ("ni", "に", "Не подходит к объекту действия."),
                    ("de", "で", "Обычно это место или средство."),
                ),
            },
            {
                "key": "basic_negative",
                "skill_label": "Отрицательная форма",
                "prompt": "Как сказать 'Я сегодня не иду'?",
                "correct": "kyou_wa_ikimasen",
                "hints": (
                    "Нужна отрицательная вежливая форма от 行きます.",
                    "Заканчивается на '-masen'.",
                    "Правильный ответ: 今日は行きません。",
                ),
                "options": (
                    (
                        "kyou_wa_ikimasen",
                        "今日は行きません。",
                        "Верная отрицательная форма.",
                    ),
                    ("kyou_wa_ikimasu", "今日は行きます。", "Это утверждение, не отрицание."),
                    ("kyou_wa_ikanai_desu", "今日は行かないです。", "Фраза возможна, но не тот регистр и не тот паттерн, который ожидается здесь."),
                ),
            },
            {
                "key": "basic_order_food",
                "skill_label": "Бытовые сцены",
                "prompt": "Что естественнее сказать в кафе, если ты заказываешь воду?",
                "correct": "mizu_onegaishimasu",
                "hints": (
                    "Это короткая бытовая реплика заказа.",
                    "В ответе есть 'onegaishimasu'.",
                    "Правильный ответ: 水お願いします。",
                ),
                "options": (
                    (
                        "mizu_onegaishimasu",
                        "水お願いします。",
                        "Естественный короткий заказ.",
                    ),
                    ("mizu_desu", "水です。", "Это не заказ."),
                    ("mizu_ni_ikimasu", "水に行きます。", "Фраза сломана по смыслу."),
                ),
            },
        ),
    },
    LanguageLevel.INTERMEDIATE: {
        "title": "Уверенный срез",
        "description": "Проверяет различие регистров, связность и более точный выбор формы.",
        "questions": (
            {
                "key": "intermediate_keigo",
                "skill_label": "Регистр речи",
                "prompt": "Какой вариант звучит уместнее в разговоре с клиентом: 'Я понял'?",
                "correct": "shouchi_shimashita",
                "hints": (
                    "Нужен более деловой и уважительный вариант.",
                    "Это не просто 'wakarimashita'.",
                    "Правильный ответ: 承知しました。",
                ),
                "options": (
                    (
                        "shouchi_shimashita",
                        "承知しました。",
                        "Более уместный деловой вариант.",
                    ),
                    ("wakatta", "わかった。", "Слишком разговорно."),
                    ("wakarimashita", "わかりました。", "Вежливо, но менее формально."),
                ),
            },
            {
                "key": "intermediate_connector",
                "skill_label": "Связность фразы",
                "prompt": "Как лучше связать фразы: 'Шел дождь, поэтому поезд опоздал'?",
                "correct": "ame_ga_futta_node_densha_ga_okuremashita",
                "hints": (
                    "Нужна причинно-следственная связка.",
                    "Ищи вариант с 'node'.",
                    "Правильный ответ: 雨が降ったので電車が遅れました。",
                ),
                "options": (
                    (
                        "ame_ga_futta_node_densha_ga_okuremashita",
                        "雨が降ったので電車が遅れました。",
                        "Естественная причинная связка.",
                    ),
                    (
                        "ame_ga_futta_densha_ga_okuremashita",
                        "雨が降った電車が遅れました。",
                        "Связка ломает смысл.",
                    ),
                    (
                        "ame_ga_futta_kedo_densha_ga_okuremashita",
                        "雨が降ったけど電車が遅れました。",
                        "Можно понять, но союз здесь слабее и не точнее по смыслу.",
                    ),
                ),
            },
            {
                "key": "intermediate_reading",
                "skill_label": "Чтение канжи в контексте",
                "prompt": "Как читается 会社員?",
                "correct": "kaishain",
                "hints": (
                    "Это слово про офисную работу.",
                    "Чтение начинается на 'kai'.",
                    "Правильный ответ: kaishain.",
                ),
                "options": (
                    ("kaishain", "かいしゃいん", "Нормальное чтение слова."),
                    ("gaishain", "がいしゃいん", "Начало читается не так."),
                    ("kaijain", "かいじゃいん", "Середина чтения ломается."),
                ),
            },
            {
                "key": "intermediate_intent",
                "skill_label": "Намерение и план",
                "prompt": "Какой вариант точнее передает 'Я собираюсь учиться в Японии'?",
                "correct": "nihon_de_benkyou_shiyou_to_omotteimasu",
                "hints": (
                    "Нужна конструкция про намерение.",
                    "Ищи форму с 'to omotteimasu'.",
                    "Правильный ответ: 日本で勉強しようと思っています。",
                ),
                "options": (
                    (
                        "nihon_de_benkyou_shiyou_to_omotteimasu",
                        "日本で勉強しようと思っています。",
                        "Точный вариант для намерения.",
                    ),
                    (
                        "nihon_de_benkyou_shimasu",
                        "日本で勉強します。",
                        "Это просто план как факт, без акцента на намерение.",
                    ),
                    (
                        "nihon_de_benkyou_shitai_desu",
                        "日本で勉強したいです。",
                        "Желание, но не та конструкция, которую ждут здесь.",
                    ),
                ),
            },
            {
                "key": "intermediate_context",
                "skill_label": "Точность в контексте",
                "prompt": "Какой ответ уместнее, если ты опоздал на встречу и хочешь кратко извиниться?",
                "correct": "osoku_nattek_shitsurei_shimashita",
                "hints": (
                    "Нужен короткий формальный ответ.",
                    "В ответе есть 'shitsurei shimashita'.",
                    "Правильный ответ: 遅くなって失礼しました。",
                ),
                "options": (
                    (
                        "osoku_nattek_shitsurei_shimashita",
                        "遅くなって失礼しました。",
                        "Краткое и уместное извинение.",
                    ),
                    ("sumimasen_deshita", "すみませんでした。", "Понять можно, но здесь менее точный выбор."),
                    ("mada_ikimasu", "まだ行きます。", "Смысл не совпадает."),
                ),
            },
        ),
    },
}


def build_onboarding_question_groups() -> list[DiagnosticQuestionGroupDTO]:
    groups: list[DiagnosticQuestionGroupDTO] = []
    for level in LanguageLevel:
        bank = _DIAGNOSTIC_BANKS[level]
        groups.append(
            DiagnosticQuestionGroupDTO(
                level=level.value,
                title=bank["title"],
                description=bank["description"],
                questions=[_to_question_dto(item) for item in bank["questions"]],
            )
        )
    return groups


def build_study_timeline_options() -> list[StudyTimelineOptionDTO]:
    options = (
        (
            StudyTimeline.THREE_MONTHS,
            "3 месяца",
            "Сжатый режим: только ядро языка, выше плотность и меньше лирики.",
        ),
        (
            StudyTimeline.SIX_MONTHS,
            "6 месяцев",
            "Интенсивный темп: база и речь собираются быстро, но без перегруза каждым правилом.",
        ),
        (
            StudyTimeline.ONE_YEAR,
            "1 год",
            "Сбалансированный режим: можно объяснять подробнее и закреплять материал работами.",
        ),
        (
            StudyTimeline.TWO_YEARS,
            "2 года+",
            "Глубокий темп: больше контекста, чтения и спокойного наращивания сложности.",
        ),
        (
            StudyTimeline.FLEXIBLE,
            "Без дедлайна",
            "Гибкий режим: система сильнее подстраивается под реальные просадки, а не под календарь.",
        ),
    )
    return [
        StudyTimelineOptionDTO(
            value=item.value,
            title=title,
            description=description,
        )
        for item, title, description in options
    ]


def evaluate_diagnostic_answers(
    answers: dict[str, str],
    declared_level: LanguageLevel,
    hints_used: int = 0,
) -> SkillAssessment:
    bank = _DIAGNOSTIC_BANKS[declared_level]["questions"]
    normalized_answers = {
        key: value.strip()
        for key, value in answers.items()
        if value and value.strip()
    }
    missing = [item["key"] for item in bank if item["key"] not in normalized_answers]
    if missing:
        raise ValueError("Нужно ответить на все 5 быстрых вопросов")

    raw_score = 0
    strengths: list[str] = []
    weak_points: list[str] = []
    for item in bank:
        label = item["skill_label"]
        if normalized_answers[item["key"]] == item["correct"]:
            raw_score += 1
            strengths.append(label)
        else:
            weak_points.append(label)

    penalty = min(2, hints_used // 2)
    score = max(0, raw_score - penalty)
    estimated_level = _level_from_score(declared_level, score)
    summary = _build_summary(
        raw_score=raw_score,
        penalty=penalty,
        declared_level=declared_level,
        estimated_level=estimated_level,
        strengths=strengths,
        weak_points=weak_points,
        hints_used=hints_used,
    )
    return SkillAssessment(
        score=score,
        estimated_level=estimated_level,
        summary=summary,
        strengths=strengths,
        weak_points=weak_points,
    )


def _to_question_dto(item: dict) -> DiagnosticQuestionDTO:
    return DiagnosticQuestionDTO(
        key=item["key"],
        prompt=item["prompt"],
        skill_label=item["skill_label"],
        options=[
            DiagnosticOptionDTO(
                value=value,
                label=label,
                description=description,
            )
            for value, label, description in item["options"]
        ],
        hints=list(item.get("hints") or []),
    )


def _level_from_score(declared_level: LanguageLevel, score: int) -> LanguageLevel:
    if declared_level == LanguageLevel.ZERO:
        if score <= 2:
            return LanguageLevel.ZERO
        if score <= 4:
            return LanguageLevel.BASIC
        return LanguageLevel.INTERMEDIATE
    if declared_level == LanguageLevel.BASIC:
        if score <= 1:
            return LanguageLevel.ZERO
        if score <= 3:
            return LanguageLevel.BASIC
        return LanguageLevel.INTERMEDIATE
    if score <= 1:
        return LanguageLevel.BASIC
    return LanguageLevel.INTERMEDIATE


def _build_summary(
    *,
    raw_score: int,
    penalty: int,
    declared_level: LanguageLevel,
    estimated_level: LanguageLevel,
    strengths: list[str],
    weak_points: list[str],
    hints_used: int,
) -> str:
    adjusted_score = max(0, raw_score - penalty)
    parts = [
        f"Быстрый тест: {raw_score}/5.",
        f"Самооценка: {_level_title(declared_level)}.",
        f"Текущий старт ближе к уровню '{_level_title(estimated_level)}'.",
    ]
    if hints_used:
        parts.append(
            f"Подсказки использовались {hints_used} раз, поэтому доверие к стартовому срезу снижено на {penalty} балл(а)."
        )
    parts.append(f"В расчет trust score уйдет {adjusted_score}/5.")
    if strengths:
        parts.append(f"Лучше всего держатся: {', '.join(strengths)}.")
    if weak_points:
        parts.append(f"Проседают: {', '.join(weak_points)}.")
    return " ".join(parts)


def _level_title(level: LanguageLevel) -> str:
    return {
        LanguageLevel.ZERO: "стартовый",
        LanguageLevel.BASIC: "базовый",
        LanguageLevel.INTERMEDIATE: "уверенный",
    }[level]
