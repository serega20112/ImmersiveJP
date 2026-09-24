"""
Юнит-тесты разбора результатов проверки знаний.

Проверяется различие, которого раньше не было: вопрос без вердикта модели и
вопрос с вердиктом «неверно» — это разные ситуации для пользователя. Раньше
отсутствие вердикта получало текст «Ответ не совпал с ожидаемым», то есть сбой
проверки выдавался за ошибку ученика.
"""

from src.infrastructures.external.llm.client import HuggingFaceLLMClient

QUESTIONS = [
    {"id": "q1", "question": "Как будет «вода»?", "expected_answer": "水"},
    {"id": "q2", "question": "Частица темы?", "expected_answer": "は"},
]
ANSWERS = {"q1": "水", "q2": "が"}


def evaluate(parsed: object) -> dict:
    """Разобрать ответ модели по фиксированным вопросам и ответам.

    Args:
        parsed: Разобранный ответ модели.

    Returns:
        Итог проверки.
    """
    return HuggingFaceLLMClient._normalize_knowledge_eval(parsed, QUESTIONS, ANSWERS)


def result_by_id(results: list[dict], question_id: str) -> dict:
    """Найти разбор конкретного вопроса.

    Args:
        results: Список разборов по вопросам.
        question_id: Идентификатор вопроса.

    Returns:
        Разбор вопроса.

    Raises:
        KeyError: Если вопроса нет в разборе.
    """
    for item in results:
        if item["question_id"] == question_id:
            return item
    raise KeyError(question_id)


class TestVerdictPresence:
    """Группа тестов различения вердикта и его отсутствия."""

    def test_missing_verdict_is_reported_as_check_failure(self) -> None:
        """
        Тестируем: вопрос, по которому модель ничего не вернула.
        Отдаём: results только по первому вопросу.
        Ожидаем: по второму feedback «Не удалось проверить», а не «не совпал».
        """
        parsed = {
            "results": [{"question_id": "q1", "is_correct": True, "feedback": "Верно"}],
            "summary": "",
        }

        results = evaluate(parsed)["results"]

        assert result_by_id(results, "q2")["feedback"] == "Не удалось проверить."
        assert result_by_id(results, "q2")["is_correct"] is False

    def test_negative_verdict_keeps_mismatch_wording(self) -> None:
        """
        Тестируем: явно выставленный неверный ответ без текста обратной связи.
        Отдаём: is_correct false без feedback.
        Ожидаем: формулировка про несовпадение, а не про сбой проверки.
        """
        parsed = {"results": [{"question_id": "q1", "is_correct": False}], "summary": "ок"}

        results = evaluate(parsed)["results"]

        assert result_by_id(results, "q1")["feedback"] == "Ответ не совпал с ожидаемым."

    def test_empty_object_verdict_is_a_failure_not_a_grade(self) -> None:
        """
        Тестируем: пустой объект вердикта.
        Отдаём: results с элементом без полей.
        Ожидаем: вопрос засчитан как непроверенный.
        """
        parsed = {"results": [{}], "summary": ""}

        results = evaluate(parsed)["results"]

        assert all(item["feedback"] == "Не удалось проверить." for item in results)


class TestScoring:
    """Группа тестов итоговой оценки и сводки."""

    def test_score_counts_only_confirmed_correct_answers(self) -> None:
        """
        Тестируем: оценку при одном верном и одном непроверенном ответе.
        Отдаём: is_correct true по первому вопросу, тишина по второму.
        Ожидаем: 50 процентов и сводка о числе правильных.
        """
        parsed = {"results": [{"question_id": "q1", "is_correct": True}], "summary": ""}

        outcome = evaluate(parsed)

        assert outcome["score"] == 50
        assert outcome["summary"] == "Правильно: 1 из 2."

    def test_model_summary_wins_over_generated_one(self) -> None:
        """
        Тестируем: сводку из ответа модели.
        Отдаём: непустой summary.
        Ожидаем: он же, сгенерированный текст не перекрывает ответ.
        """
        parsed = {
            "results": [{"question_id": "q1", "is_correct": True}],
            "summary": "Хорошо держишь лексику.",
        }

        assert evaluate(parsed)["summary"] == "Хорошо держишь лексику."

    def test_unparseable_results_yield_zero_without_crash(self) -> None:
        """
        Тестируем: поле results не того типа.
        Отдаём: строку вместо списка вердиктов.
        Ожидаем: оценка ноль, все вопросы непроверены, исключения нет.
        """
        parsed = {"results": "модель выдала текст", "summary": ""}

        outcome = evaluate(parsed)

        assert outcome["score"] == 0
        assert len(outcome["results"]) == 2

    def test_results_alias_key_is_read(self) -> None:
        """
        Тестируем: альтернативное имя поля с результатами.
        Отдаём: объект с ключом result вместо results.
        Ожидаем: вердикт прочитан, вопрос засчитан правильным.
        """
        parsed = {"result": [{"question_id": "q1", "is_correct": True}], "summary": ""}

        results = evaluate(parsed)["results"]

        assert result_by_id(results, "q1")["is_correct"] is True


class TestAnswerEchoing:
    """Группа тестов возврата пользователю его же ответа."""

    def test_user_and_expected_answers_are_returned(self) -> None:
        """
        Тестируем: перенос ответа ученика и ожидаемого ответа в разбор.
        Отдаём: два вопроса и ответы к ним.
        Ожидаем: оба поля на месте по каждому вопросу.
        """
        parsed = {
            "results": [
                {"question_id": "q1", "is_correct": True, "feedback": "Верно"},
                {"question_id": "q2", "is_correct": False, "feedback": "Не та частица"},
            ],
            "summary": "",
        }

        results = evaluate(parsed)["results"]

        assert result_by_id(results, "q1")["user_answer"] == "水"
        assert result_by_id(results, "q1")["expected_answer"] == "水"
        assert result_by_id(results, "q2")["feedback"] == "Не та частица"

    def test_absent_answer_becomes_empty_string(self) -> None:
        """
        Тестируем: вопрос, на который ответа не было.
        Отдаём: answers без идентификатора второго вопроса.
        Ожидаем: пустая строка вместо KeyError или None.
        """
        parsed = {"results": [], "summary": ""}

        outcome = HuggingFaceLLMClient._normalize_knowledge_eval(parsed, QUESTIONS, {"q1": "水"})

        assert result_by_id(outcome["results"], "q2")["user_answer"] == ""
