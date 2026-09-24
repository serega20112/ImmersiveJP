"""
Юнит-тесты извлечения JSON из ответа модели.

Проверяется разбор первого JSON-документа в тексте, где возможны markdown и
пояснения. Исторический дефект: фиксированный приоритет квадратной скобки
попадал во вложенный массив ответа {"focus_points": [...]}, разбор проходил
успешно, и верхнеуровневый объект не читался ни разу — пять функций из шести
молча уходили в заготовки. Здесь зафиксировано именно это поведение, чтобы
возврат к старому порядку скобок не остался незамеченным.
"""

import pytest

from src.infrastructures.external.llm.client import HuggingFaceLLMClient


class TestExtractJsonObjectFirst:
    """Группа тестов выбора объекта корнем при вложенном массиве."""

    def test_object_with_nested_array_returns_object(self) -> None:
        """
        Тестируем: ответ advice-формы с вложенным массивом.
        Отдаём: строку {"headline": ..., "focus_points": [...]} без пробела перед '['.
        Ожидаем: возвращается dict, а не внутренний массив.
        """
        raw_content = '{"headline": "Шаг", "focus_points": ["раз", "два", "три"]}'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert isinstance(parsed, dict)
        assert parsed["headline"] == "Шаг"
        assert parsed["focus_points"] == ["раз", "два", "три"]

    def test_object_with_pretty_printed_nested_array(self) -> None:
        """
        Тестируем: то же поведение в многострочном формате.
        Отдаём: объект, где вложенный массив начинается раньше закрывающей скобки.
        Ожидаем: возвращается dict с полным содержимым.
        """
        raw_content = (
            '{\n  "reply": "ок",\n  "action_steps": [\n    "первый",\n    "второй"\n  ]\n}'
        )

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert isinstance(parsed, dict)
        assert parsed["action_steps"] == ["первый", "второй"]

    def test_markdown_fence_with_object(self) -> None:
        """
        Тестируем: объект внутри markdown-обёртки.
        Отдаём: код-блок с JSON-объектом.
        Ожидаем: обёртка не мешает, возвращается dict.
        """
        raw_content = '```json\n{"score": 80, "summary": "норм"}\n```'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert parsed == {"score": 80, "summary": "норм"}

    def test_prose_before_object(self) -> None:
        """
        Тестируем: пояснение перед JSON.
        Отдаём: текст ответа и объект после него.
        Ожидаем: возвращается dict.
        """
        raw_content = 'Конечно! Вот результат: {"reply": "привет"}'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert parsed == {"reply": "привет"}


class TestExtractJsonListFirst:
    """Группа тестов выбора массива корнем."""

    def test_top_level_array(self) -> None:
        """
        Тестируем: партии карточек, где корень — массив.
        Отдаём: JSON-массив объектов.
        Ожидаем: возвращается list той же длины.
        """
        raw_content = '[{"topic": "А"}, {"topic": "Б"}]'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_array_positioned_before_object(self) -> None:
        """
        Тестируем: массив встречается в тексте раньше объекта.
        Отдаём: массив, затем полноценный объект.
        Ожидаем: корнем становится тот, что левее, то есть list.
        """
        raw_content = '[1, 2, 3] {"a": 1}'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert parsed == [1, 2, 3]

    def test_broken_object_falls_back_to_valid_array(self) -> None:
        """
        Тестируем: разбор от объекта не удаётся, а массив разбивается.
        Отдаём: битый объект и корректный массив после него.
        Ожидаем: возвращается list, а не исключение.
        """
        raw_content = '{"a": } [{"b": 1}]'

        parsed = HuggingFaceLLMClient._extract_json(raw_content)

        assert parsed == [{"b": 1}]


class TestExtractJsonFailure:
    """Группа тестов отказа разбора."""

    def test_no_json_raises(self) -> None:
        """
        Тестируем: ответ без каких-либо скобок.
        Отдаём: обычную фразу.
        Ожидаем: ValueError с понятным текстом, молчаливого None не допускается.
        """
        with pytest.raises(ValueError, match="JSON payload was not found"):
            HuggingFaceLLMClient._extract_json("модель ответила текстом без JSON")

    def test_only_malformed_candidates_raise(self) -> None:
        """
        Тестируем: обе скобки есть, но ни одна не разбирается.
        Отдаём: обрывки JSON.
        Ожидаем: ValueError, а не частичный результат.
        """
        with pytest.raises(ValueError, match="JSON payload was not found"):
            HuggingFaceLLMClient._extract_json("{oops [unclosed")


class TestCoercion:
    """Группа тестов приведения разобранного к нужной форме."""

    def test_coerce_object_unwraps_known_envelope(self) -> None:
        """
        Тестируем: снятие служебной обёртки ответа.
        Отдаём: {"response": {"reply": "текст"}}.
        Ожидаем: возвращается внутренняя оболочка.
        """
        parsed = {"response": {"reply": "текст"}}

        assert HuggingFaceLLMClient._coerce_object(parsed) == {"reply": "текст"}

    def test_coerce_object_takes_first_mapping_from_list(self) -> None:
        """
        Тестируем: объект внутри массива.
        Отдаём: [{...}, "..."].
        Ожидаем: возвращается первый dict списка.
        """
        parsed = [{"reply": "первый"}, "лишнее"]

        assert HuggingFaceLLMClient._coerce_object(parsed) == {"reply": "первый"}

    def test_coerce_list_reads_known_keys(self) -> None:
        """
        Тестируем: массив под служебным ключом.
        Отдаём: {"cards": [{...}]}.
        Ожидаем: возвращается содержимое ключа cards.
        """
        parsed = {"cards": [{"topic": "Т"}]}

        assert HuggingFaceLLMClient._coerce_list(parsed) == [{"topic": "Т"}]

    def test_coerce_list_wraps_bare_object(self) -> None:
        """
        Тестируем: одиночный объект там, где ждём список.
        Отдаём: {"topic": "Т"}.
        Ожидаем: объект становится одноэлементным списком, а не теряется.
        """
        parsed = {"topic": "Т"}

        assert HuggingFaceLLMClient._coerce_list(parsed) == [{"topic": "Т"}]

    def test_coerce_rejects_scalars(self) -> None:
        """
        Тестируем: скаляр вместо структуры.
        Отдаём: число.
        Ожидаем: TypeError, потому что молчаливый пустой список скрыл бы дефект.
        """
        with pytest.raises(TypeError):
            HuggingFaceLLMClient._coerce_list(7)
