"""Юнит-тесты сущности UserDocument: структура пользовательского конспекта."""

from src.domain.entities.documents import UserDocument
from src.domain.value_objects import DocumentTitle, Timestamp, UserID


class TestUserDocument:
    """Группа тестов пользовательского документа."""

    def test_holds_fields(self) -> None:
        """
        Тестируем: структуру документа.
        Отдаём: валидные user_id, title, content и время создания.
        Ожидаем: документ хранит переданные значения, id по умолчанию None.
        """
        document = UserDocument(
            user_id=UserID(1),
            title=DocumentTitle("Конспект"),
            content="Текст конспекта",
            created_at=Timestamp.now(),
        )

        assert document.id is None
        assert document.title.value == "Конспект"
        assert document.content == "Текст конспекта"
