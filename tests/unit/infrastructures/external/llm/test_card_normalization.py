"""
Юнит-тесты нормализации партии карточек из ответа модели.

Проверяется поведение, ради которого нормализация была переписана: карточка
модели не выбрасывается из-за малого числа примеров, дубликаты ищутся по теме,
а недостающее добирается заготовками честно, с разделением по источнику.
Раньше подстановка шаблонных примеров делала их одинаковыми, дедупликация по
подписи примеров уничтожила живые карточки, и партия пришла из заготовок,
выдавая себя за генерацию.
"""

from src.infrastructures.external.llm.client import HuggingFaceLLMClient

JAPANESE_EXAMPLE = "私は学生です。 | watashi wa gakusei desu. | Я студент."


def cards_payload(track: str, batch_size: int) -> dict:
    """Собрать контекст нормализации партии.

    Args:
        track: Ключ трека.
        batch_size: Размер партии.

    Returns:
        Payload для _normalize_cards.
    """
    return {
        "track": track,
        "batch_size": batch_size,
        "batch_number": 1,
        "interests": ["музыка"],
        "goal": "travel",
        "language_level": "beginner",
        "study_timeline": "one_month",
        "diagnostic_summary": "короткая сводка",
    }


def model_card(topic: str, *, examples: list[str] | None = None) -> dict:
    """Собрать карточку в форме ответа модели.

    Args:
        topic: Тема карточки.
        examples: Примеры употребления.

    Returns:
        Словарь карточки.
    """
    return {
        "topic": topic,
        "explanation": f"Объяснение темы {topic} с фразой и лексикой.",
        "examples": examples if examples is not None else [JAPANESE_EXAMPLE],
        "key_terms": ["学生", "は"],
    }


class TestModelCardsSurvive:
    """Группа тестов сохранения карточек, пришедших от модели."""

    def test_full_batch_is_attributed_to_model(self) -> None:
        """
        Тестируем: партию, которую модель отдала целиком.
        Отдаём: пять корректных карточек language-трека.
        Ожидаем: пять черновиков, model_count равен пяти, заготовок нет.
        """
        parsed = [model_card(f"Тема {index}") for index in range(1, 6)]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 5))

        assert len(batch.drafts) == 5
        assert batch.model_count == 5
        assert batch.fallback_count == 0
        assert batch.is_all_from_model is True

    def test_card_with_single_example_is_not_dropped(self) -> None:
        """
        Тестируем: карточку с одним примером.
        Отдаём: language-партию из двух карточек, у одной пример единственный.
        Ожидаем: обе карточки сохранены как модельные, пример не подменён.
        """
        parsed = [
            model_card("Вежливые просьбы", examples=["水をください。 | mizu o kudasai."]),
            model_card("Частицы", examples=[JAPANESE_EXAMPLE]),
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 2))

        assert [draft.topic for draft in batch.drafts] == ["Вежливые просьбы", "Частицы"]
        assert batch.drafts[0].examples == ["水をください。 | mizu o kudasai."]
        assert batch.model_count == 2

    def test_two_cards_with_identical_examples_both_survive(self) -> None:
        """
        Тестируем: разные темы с одинаковым примером.
        Отдаём: две карточки с одним и тем же текстом примера.
        Ожидаем: обе остались — дедупликация по подписи примеров убивала их как дубликаты.
        """
        parsed = [
            model_card("Тема первая", examples=[JAPANESE_EXAMPLE]),
            model_card("Тема вторая", examples=[JAPANESE_EXAMPLE]),
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 2))

        assert len(batch.drafts) == 2
        assert batch.model_count == 2
        assert batch.fallback_count == 0

    def test_batch_size_caps_longer_response(self) -> None:
        """
        Тестируем: ответ длиннее запрошенной партии.
        Отдаём: восемь карточек при размере партии пять.
        Ожидаем: ровно пять карточек в порядке ответа.
        """
        parsed = [model_card(f"Тема {index}") for index in range(1, 9)]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 5))

        assert len(batch.drafts) == 5
        assert batch.model_count == 5


class TestCardRejections:
    """Группа тестов отбраковки непригодных карточек."""

    def test_duplicate_topic_is_dropped(self) -> None:
        """
        Тестируем: повтор той же темы.
        Отдаём: две карточки с одинаковой темой.
        Ожидаем: одна карточка от модели, остальное добирается заготовками.
        """
        parsed = [model_card("Одна и та же тема"), model_card("Одна и та же тема")]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 1))

        assert batch.model_count == 1
        assert len(batch.drafts) == 1

    def test_empty_topic_is_dropped(self) -> None:
        """
        Тестируем: карточку без темы.
        Отдаём: объект с пустым topic и одну корректную карточку.
        Ожидаем: пустая тема отброшена, партия сложилась из заготовки.
        """
        parsed = [{"topic": "  ", "explanation": "текст"}, model_card("Живая тема")]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 1))

        assert batch.model_count == 1
        assert batch.drafts[0].topic == "Живая тема"

    def test_placeholder_topic_is_dropped(self) -> None:
        """
        Тестируем: служебную тему-заполнитель из старых ответов.
        Отдаём: карточку с темой «Резервная тема 3».
        Ожидаем: она не попадает в партию как модельная.
        """
        parsed = [
            {
                "topic": "Резервная тема 3",
                "explanation": "Заполнитель.",
                "examples": [JAPANESE_EXAMPLE],
                "key_terms": ["語"],
            }
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 1))

        assert batch.model_count == 0
        assert batch.fallback_count == 1

    def test_offtopic_language_card_is_filtered(self) -> None:
        """
        Тестируем: language-карточку без японского и без признаков языка.
        Отдаём: текст про горный пейзаж.
        Ожидаем: карточка отсеяна как не относящаяся к треку.
        """
        parsed = [
            {
                "topic": "Гора Фудзи зимой",
                "explanation": "Красивое природное явление в горах.",
                "examples": [],
                "key_terms": ["гора", "зима"],
            }
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 1))

        assert batch.model_count == 0

    def test_culture_card_about_grammar_is_filtered(self) -> None:
        """
        Тестируем: culture-карточку, целиком про грамматику и ромадзи.
        Отдаём: текст без признаков бытовой культуры.
        Ожидаем: карточка отсеяна как ушедшая в чужой трек.
        """
        parsed = [
            {
                "topic": "Грамматика частиц",
                "explanation": "Разбор грамматики и чтение ромадзи с переводом фраз.",
                "examples": [],
                "key_terms": ["частицы"],
            }
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("culture", 1))

        assert batch.model_count == 0

    def test_culture_card_without_signal_words_is_kept(self) -> None:
        """
        Тестируем: culture-карточку без служебных слов трека.
        Отдаём: текст про обувь у входа, где нет слова «культура».
        Ожидаем: карточка сохранена — проверка не белый список.
        """
        parsed = [
            {
                "topic": "Обувь у входа",
                "explanation": "Перед домом обувь снимают, и это замечают сразу.",
                "examples": [],
                "key_terms": ["обувь"],
            }
        ]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("culture", 1))

        assert batch.model_count == 1


class TestFallbackAttribution:
    """Группа тестов честного разделения источника партии."""

    def test_shortfall_is_counted_as_fallback(self) -> None:
        """
        Тестируем: партию, которую модель не довела до размера.
        Отдаём: две карточки при запросе на пять.
        Ожидаем: пять черновиков, из них два от модели и три заготовки.
        """
        parsed = [model_card("Тема одна"), model_card("Тема две")]

        batch = HuggingFaceLLMClient._normalize_cards(parsed, cards_payload("language", 5))

        assert len(batch.drafts) == 5
        assert batch.model_count == 2
        assert batch.fallback_count == 3
        assert batch.is_all_from_model is False

    def test_empty_response_is_all_fallback(self) -> None:
        """
        Тестируем: пустой ответ модели.
        Отдаём: пустой список.
        Ожидаем: партия целиком из заготовок и не числится модельной.
        """
        batch = HuggingFaceLLMClient._normalize_cards([], cards_payload("culture", 3))

        assert len(batch.drafts) == 3
        assert batch.model_count == 0
        assert batch.fallback_count == 3

    def test_fallback_cards_have_distinct_topics(self) -> None:
        """
        Тестируем: темы заготовочной партии.
        Отдаём: пустой ответ и запрос на три карточки.
        Ожидаем: темы не повторяются, иначе дедупликация съела бы карточки.
        """
        batch = HuggingFaceLLMClient._normalize_cards([], cards_payload("language", 3))

        topics = [draft.topic for draft in batch.drafts]

        assert len(set(topics)) == 3
