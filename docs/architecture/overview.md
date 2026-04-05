# Обзор архитектуры

ImmersJP собран как асинхронный FastAPI-проект с серверным рендерингом через Jinja2.

Основные слои:

- `delivery` — FastAPI route в `src/backend/delivery/api/v1` и HTML-ответы. Логика здесь не живет.
- `dependencies` — контейнер зависимостей и request-scope.
- `services` — тонкие делегаты между route и use case.
- `use_case` — сценарии приложения: регистрация, онбординг, генерация карточек, прогресс, PDF.
- `domain` — сущности и продуктовые типы.
- `infrastructure` — БД, Redis, JWT, email, LLM, PDF, шаблонизация.
- `repository` — concrete-репозитории с SQLAlchemy-логикой. Они наследуются от абстракций в `infrastructure/repositories`.

Контейнер зависимостей работает в двух слоях:

- process-wide singletons: Redis store, JWT, password hashing, mailer, LLM client, PDF builder;
- request-scoped objects: `AsyncSession`, concrete repositories, use case, services.

DTO используются как явные контракты между route, services и use case. Доменные сущности наружу не торчат.

Route подключаются напрямую в `create_app.py` без отдельного агрегирующего router-модуля.
