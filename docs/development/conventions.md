# Конвенции разработки

- Route остаются тонкими: получают входные данные, вызывают service, возвращают HTML или redirect.
- Route лежат в `src/backend/delivery/api/v1` и подключаются напрямую в `create_app.py`.
- В `services` нет бизнес-логики. Это делегаты над use case.
- Репозитории с SQLAlchemy-логикой лежат в `src/backend/repository`.
- Абстракции репозиториев лежат в `src/backend/infrastructure/repositories`.
- Use case содержат правила приложения и orchestration.
- Все новые изменения схемы идут через Alembic revision, а не через `create_all`.
- `__init__.py` используются как явные import-point без `__all__`.
