# Docker и запуск

## Локальный запуск (без Docker)

```powershell
# 1. Скопировать .env
cp .env.example .env

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить PostgreSQL и Redis (вручную или через Docker)
#    docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=immersjp postgres:16
#    docker run -d -p 6379:6379 redis:7

# 4. Прогнать миграции
alembic -c build/alembic/alembic.ini upgrade head

# 5. Запустить
python -m src.main
```

Приложение будет на `http://localhost:8000`.

## Docker Compose

```powershell
docker compose up --build
```

Поднимает три контейнера:

| Сервис | Образ | Порт |
|--------|-------|------|
| `app` | Из `Dockerfile` | `8000` |
| `postgres` | `postgres:16-alpine` | `5432` |
| `redis` | `redis:7-alpine` | `6379` |

В контейнере приложение запускается через `uvicorn src.main:app`. Миграции прогоняются автоматически перед стартом через скрипт, указанный в `Dockerfile`.

## Переменные окружения

Все настройки — через `.env`. Обязательные:

| Переменная | Описание |
|------------|----------|
| `SECRET_KEY` | Ключ для подписи JWT (≥16 символов в production) |
| `SESSION_SECRET` | Ключ для подписи cookie-сессий |

Опциональные:

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `APP_HOST` | `0.0.0.0` | Хост приложения |
| `APP_PORT` | `8000` | Порт |
| `APP_DEBUG` | `false` | Режим отладки |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `DATABASE_URL` | автосборка | Полный URL для async-драйвера |
| `REDIS_URL` | `redis://localhost:6379/0` | URL Redis |
| `REDIS_REQUIRED` | `false` | Падать ли без Redis |
| `ELASTICSEARCH_ENABLED` | `false` | Включить отправку логов в ES |
| `ELASTICSEARCH_URL` | — | URL Elasticsearch |
| `HF_API_TOKEN` | — | Токен OpenRouter / HuggingFace |
| `SMTP_*` | — | Настройки почты для отправки кодов |

Полный список — в `src/backend/dependencies/settings_model.py`.
