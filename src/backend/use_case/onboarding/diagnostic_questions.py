from __future__ import annotations

from src.backend.domain.user import LanguageLevel, SkillAssessment
from src.backend.dto.onboarding_dto import DiagnosticOptionDTO, DiagnosticQuestionDTO


_DIAGNOSTIC_ITEMS = (
    {
        "key": "reading_ka",
        "skill_label": "Хирагана",
        "prompt": "Как читается か?",
        "correct": "ka",
        "options": (
            ("ka", "ка", "Базовое чтение слога か."),
            ("e", "э", "Путает хирагану с другим знаком."),
            ("ke", "кэ", "Ошибка в чтении начального слога."),
        ),
    },
    {
        "key": "word_mizu",
        "skill_label": "Базовая лексика",
        "prompt": "Что означает みず?",
        "correct": "water",
        "options": (
            ("water", "вода", "Понимает базовую бытовую лексику."),
            ("train", "поезд", "Путает бытовые слова."),
            ("window", "окно", "Пока не держит базовый словарь."),
        ),
    },
    {
        "key": "polite_thanks",
        "skill_label": "Формулы вежливости",
        "prompt": "Какой вариант звучит как более вежливое 'спасибо'?",
        "correct": "arigatou_gozaimasu",
        "options": (
            (
                "arigatou_gozaimasu",
                "ありがとうございます",
                "Чувствует разницу между нейтральной и вежливой формой.",
            ),
            (
                "arigatou",
                "ありがとう",
                "Более простая разговорная форма.",
            ),
            (
                "ohayou",
                "おはよう",
                "Это приветствие, а не благодарность.",
            ),
        ),
    },
    {
        "key": "particle_direction",
        "skill_label": "Частицы",
        "prompt": "Какая частица показывает направление в 東京に行きます?",
        "correct": "ni",
        "options": (
            ("ni", "に", "Частица направления и точки назначения."),
            ("wa", "は", "Тематическая частица, не направление."),
            ("o", "を", "Маркер прямого дополнения."),
        ),
    },
    {
        "key": "sentence_student",
        "skill_label": "Базовый порядок предложения",
        "prompt": "Какой вариант означает 'Я студент'?",
        "correct": "watashi_wa_gakusei_desu",
        "options": (
            (
                "watashi_wa_gakusei_desu",
                "私は学生です。",
                "Верный базовый паттерн представления себя.",
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
)


def build_onboarding_questions() -> list[DiagnosticQuestionDTO]:
    return [
        DiagnosticQuestionDTO(
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
        )
        for item in _DIAGNOSTIC_ITEMS
    ]


def evaluate_diagnostic_answers(
    answers: dict[str, str],
    declared_level: LanguageLevel,
) -> SkillAssessment:
    normalized_answers = {
        key: value.strip()
        for key, value in answers.items()
        if value and value.strip()
    }
    missing = [item["key"] for item in _DIAGNOSTIC_ITEMS if item["key"] not in normalized_answers]
    if missing:
        raise ValueError("Нужно ответить на все 5 быстрых вопросов")

    score = 0
    strengths: list[str] = []
    weak_points: list[str] = []
    for item in _DIAGNOSTIC_ITEMS:
        label = item["skill_label"]
        if normalized_answers[item["key"]] == item["correct"]:
            score += 1
            strengths.append(label)
        else:
            weak_points.append(label)

    estimated_level = _level_from_score(score)
    summary = _build_summary(score, declared_level, estimated_level, strengths, weak_points)
    return SkillAssessment(
        score=score,
        estimated_level=estimated_level,
        summary=summary,
        strengths=strengths,
        weak_points=weak_points,
    )


def _level_from_score(score: int) -> LanguageLevel:
    if score <= 1:
        return LanguageLevel.ZERO
    if score <= 3:
        return LanguageLevel.BASIC
    return LanguageLevel.INTERMEDIATE


def _build_summary(
    score: int,
    declared_level: LanguageLevel,
    estimated_level: LanguageLevel,
    strengths: list[str],
    weak_points: list[str],
) -> str:
    parts = [
        f"Быстрый тест: {score}/5.",
        f"Самооценка: {_level_title(declared_level)}.",
        f"Фактический старт сейчас ближе к уровню '{_level_title(estimated_level)}'.",
    ]
    if strengths:
        parts.append(f"Сильнее всего держатся: {', '.join(strengths)}.")
    if weak_points:
        parts.append(f"Проседают: {', '.join(weak_points)}.")
    return " ".join(parts)


def _level_title(level: LanguageLevel) -> str:
    return {
        LanguageLevel.ZERO: "стартовый",
        LanguageLevel.BASIC: "базовый",
        LanguageLevel.INTERMEDIATE: "уверенный",
    }[level]
