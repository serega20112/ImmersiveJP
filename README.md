# ImmersJP

Бесплатная адаптивная платформа погружения в Японию. ИИ собирает карточки-конспекты под цель, уровень и интересы пользователя.

## Быстрый старт

Проект использует [uv](https://docs.astral.sh/uv/) для управления зависимостями.

```powershell
# 1. Скопировать .env
cp .env.example .env

# 2. Установить зависимости (создаёт .venv и uv.lock)
uv sync

# 3. Прогнать миграции
uv run alembic -c build/alembic/alembic.ini upgrade head

# 4. Запустить
uv run python -m src.main
```

Открой `http://localhost:8000`.

### Docker

```powershell
docker compose up --build
```

## Разработка

```powershell
uv run ruff check src        # линтер
uv run ruff format src       # форматирование
uv run pytest src/tests      # тесты
```

## Структура проекта

Clean Architecture (слои зависят только внутрь):

```
src/
├── main.py                  # точка входа
├── application/             # слой приложения
│   ├── dto/                 # контракты данных между слоями
│   ├── interfaces/          # порты: репозитории и внешние клиенты (Protocol/ABC)
│   ├── services/            # сервисы-фасады над use cases
│   └── use_cases/           # бизнес-сценарии
├── config/                  # типизированная конфигурация (pydantic-settings)
├── domain/                  # доменные сущности, чистая логика без инфраструктуры
├── infrastructures/         # реализации портов
│   ├── database/            # SQLAlchemy engine, ORM-модели
│   ├── di_containers/       # DI-контейнер и провайдеры
│   ├── external/            # LLM, эмбеддинги, почта, PDF, TTS/STT
│   ├── observability/       # логирование, метрики, Elasticsearch
│   ├── repositories/        # реализации репозиториев
│   └── security/            # JWT, пароли, rate limit, blocklist
├── presentation/            # HTTP-слой
│   └── http/
│       ├── api/             # маршруты FastAPI
│       ├── web/             # middleware, CSRF, шаблонизация
│       └── app.py           # сборка приложения
├── frontend/                # шаблоны Jinja2 и статика
└── tests/                   # тесты
```

Dependency Rule: `presentation → application → domain`; инфраструктура реализует
порты из `application/interfaces` и подключается через DI.

## Конфигурация

Все настройки — через environment variables (см. `.env.example`).
Секреты (`SECRET_KEY`, `SESSION_SECRET`, API-ключи) не хранятся в коде.

Подробнее — в [документации](docs/README.md).