# ImmersJP

Бесплатная адаптивная платформа погружения в Японию. ИИ собирает карточки-конспекты под цель, уровень и интересы пользователя.

## Быстрый старт

```powershell
# 1. Скопировать .env
cp .env.example .env

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Прогнать миграции
alembic -c build/alembic/alembic.ini upgrade head

# 4. Запустить
python -m src.main
```

Открой `http://localhost:8000`.

### Docker

```powershell
docker compose up --build
```

## Структура проекта

```
src/backend/
├── delivery/        # HTTP-слой (маршруты, шаблоны)
├── dependencies/    # DI-контейнер и провайдеры
├── domain/          # Доменные сущности
├── dto/             # Контракты между слоями
├── infrastructure/  # БД, Redis, LLM, безопасность, логи
├── repository/      # Реализации репозиториев
├── services/        # Делегаты между routes и use case
├── use_case/        # Бизнес-сценарии
└── tests/           # Тесты
```

Подробнее — в [документации](docs/README.md).
