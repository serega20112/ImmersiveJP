# Docker и запуск

Локальный запуск:

1. Создай `.env` на основе `.env.example`.
2. Установи зависимости: `pip install -r requirements.txt`.
3. Прогони миграции: `alembic -c build/alembic/alembic.ini upgrade head`.
4. Запусти приложение: `python -m src.main`.

Docker Compose лежит в `build/docker-compose.yml` и поднимает:

- `app`
- `postgres`
- `redis`

Для контейнера приложение запускается через `uvicorn`, а миграции прогоняются отдельной командой `alembic upgrade head` перед стартом.
