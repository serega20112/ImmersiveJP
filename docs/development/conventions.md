# Конвенции разработки

## Архитектурные правила

- **Route тонкие** — получают входные данные, вызывают service, возвращают HTML/template или redirect. Никакой бизнес-логики в route.
- **Services тонкие** — делегируют use case. Не содержат правил приложения. Могут вызывать несколько use case или внешние клиенты (LLM, TTS).
- **Use case** — содержат бизнес-сценарии: правила, оркестрация, проверки. Единственное место, где принимаются продуктовые решения.
- **Repository** — реализации SQLAlchemy-логики. Лежат в `src/backend/repository/`.
- **Абстракции** — интерфейсы репозиториев в `src/backend/infrastructure/repositories/`. Репозитории от них наследуются.
- **Domain** — сущности и Value Object без зависимостей от инфраструктуры. Чистый Python.
- **DTO** — явные контракты между route → service → use case. Доменные сущности наружу не торчат.

## Структура файлов

- Один класс на файл (кроме маленьких сопутствующих).
- `__init__.py` — только реэкспорты для публичного API пакета.
- Все публичные функции и методы имеют type hints.
- Docstrings — для всех публичных API (Google-style).

## Работа с БД

- Все изменения схемы — через Alembic ревизии. `create_all` запрещён.
- Миграции в `build/alembic/`.
- Сессия — async (SQLAlchemy async + asyncpg).

## Код-стайл

- **Форматирование:** ruff (line-length 100, double quotes).
- **Линтер:** ruff (select: F, I, N, W, E, UP, B, SIM, ARG, C4, RUF).
- **Типизация:** mypy (строгий режим, `follow_imports = skip`).
- **Pre-commit:** ruff, mypy, trailing-whitespace, end-of-file-fixer, check-yaml.

## Логирование

- Только через `logging.getLogger(__name__)`. `print()` запрещён.
- JSON-формат через кастомный `JsonLogFormatter`.
- Ключевые события — через `log_event()` (c `event` + `extra_fields`).
- Подробнее: [logging.md](logging.md).

## Тестирование

- pytest, async тесты через `pytest-asyncio`.
- Файлы тестов: `*_test.py`.
- Фикстуры в `conftest.py`.
- Тесты изолированы — без реальной БД.
