from __future__ import annotations

from src.backend.use_case.learning.work_tasks import PreparedWorkTask, _answer_matches


def test_answer_matches_accepts_minor_romaji_variation():
    task = PreparedWorkTask(
        id="reading",
        kind="recall",
        title="Чтение",
        prompt="Запиши ромадзи для фразы: こんにちは",
        expected_format="ромадзи",
        source_topic="Приветствия",
        placeholder="",
        expected_answers=["Konnichiwa"],
    )

    assert _answer_matches(task, "konichiwa") is True


def test_answer_matches_accepts_kana_for_same_pronunciation():
    task = PreparedWorkTask(
        id="reading",
        kind="recall",
        title="Чтение",
        prompt="Запиши ромадзи для фразы: こんにちは",
        expected_format="ромадзи",
        source_topic="Приветствия",
        placeholder="",
        expected_answers=["Konnichiwa"],
    )

    assert _answer_matches(task, "こんにちは") is True


def test_answer_matches_accepts_short_russian_paraphrase_for_translation():
    task = PreparedWorkTask(
        id="meaning",
        kind="recall",
        title="Перевод",
        prompt="Переведи на русский",
        expected_format="краткий перевод",
        source_topic="Покупка билета на поезд",
        placeholder="",
        expected_answers=["Извините, прошу билет"],
    )

    assert _answer_matches(task, "Извините, можно мне билет?") is True
