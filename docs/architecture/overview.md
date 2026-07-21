# Архитектура

Асинхронный FastAPI-проект с серверным рендерингом (Jinja2), PostgreSQL, Redis и ИИ-клиентами (OpenRouter / HuggingFace).

## Слои

```
src/backend/
│
├── delivery/              # HTTP-слой
│   ├── api/v1/            #   Маршруты (FastAPI)
│   ├── api/common/        #   Общие утилиты (cookies, навигация)
│   └── mentor_routes.py   #   Маршруты ментора (v0, мигрируется)
│
├── dependencies/          # DI-контейнер
│   ├── providers/         #   Фабрики для сервисов, репозиториев, инфраструктуры
│   ├── container.py       #   Сборка контейнера
│   ├── auth_dependencies.py
│   ├── current_user.py
│   ├── request_scope.py
│   ├── service_dependencies.py
│   └── settings_model.py
│
├── domain/                # Доменные сущности и типы
│   ├── common/            #   Исключения, валидаторы
│   ├── content/           #   Типы контента (track, topic)
│   ├── mentor/            #   Диалог ментора
│   ├── progress/          #   Прогресс пользователя
│   ├── session/           #   Сессия обучения
│   └── user/              #   Пользователь, цели, уровень
│
├── dto/                   # Data Transfer Objects (контракты между слоями)
│   ├── auth_dto.py
│   ├── knowledge_dto.py
│   ├── learning/          #   Карточки, документы, речь, задания
│   ├── learning_dto.py    #   Реэкспорты из learning/
│   ├── mentor_dto.py
│   ├── onboarding_dto.py
│   ├── profile_dto.py
│   └── skill_dto.py
│
├── infrastructure/        # Внешние интеграции
│   ├── cache/             #   Redis KV-Store
│   ├── external/          #   LLM (HuggingFace, Qwen), TTS, STT, embedding, PDF, email
│   ├── files/             #   SQLAlchemy engine, session factory
│   ├── models/            #   ORM-модели SQLAlchemy
│   ├── observability/     #   JSON-logging, Elasticsearch, Prometheus metrics
│   ├── repositories/      #   Абстракции репозиториев (интерфейсы)
│   ├── security/          #   JWT, password hashing, rate limiter, CSRF, email verification
│   └── web/               #   Middleware, исключения, шаблонизатор, константы
│
├── repository/            # Конкретные реализации репозиториев (SQLAlchemy)
│   ├── user_repository.py
│   ├── content_repository.py
│   ├── progress_repository.py
│   ├── session_repository.py
│   ├── mentor_repository.py
│   └── user_document_repository.py
│
├── services/              # Тонкие делегаты между routes и use case
│   ├── auth_service.py
│   ├── dashboard_service.py
│   ├── learning_service.py
│   ├── onboarding_service.py
│   ├── profile_service.py
│   ├── knowledge_service.py
│   ├── rag_service.py
│   ├── document_service.py
│   ├── document_analysis_service.py
│   ├── mentor_service.py
│   └── tutor_service.py
│
├── use_case/              # Бизнес-сценарии
│   ├── auth/              #   Регистрация, вход, выход, верификация email
│   ├── dashboard/         #   Дашборд пользователя
│   ├── learning/          #   Генерация карточек, речевая практика, задания, PDF
│   ├── knowledge/         #   Проверка знаний
│   ├── onboarding/        #   Онбординг, диагностика
│   └── profile/           #   План обучения, отчёт, ментор, доверие
│
└── tests/                 # Тесты (pytest)
```

## Принципы

- **Route тонкие** — получают данные, вызывают service, отдают HTML/redirect. Без бизнес-логики.
- **Services тонкие** — делегируют use case. Без логики приложения.
- **Use case** — содержат правила и оркестрацию.
- **Domain** — сущности не зависят от инфраструктуры.
- **DTO** — явные контракты между слоями. Доменные сущности наружу не торчат.
- **DI-контейнер** — process-wide синглтоны (Redis, JWT, LLM) и request-scoped объекты (сессия БД, репозитории).
- **Абстракции репозиториев** в `infrastructure/repositories/`, реализации — в `repository/`.
- **__init__.py** — явные точки импорта.

## Поток запроса

```
HTTP Request → Middleware → Route → Service → Use Case → Repository → DB
                                    ↘ LLM Client, Cache, External API
Route ← Template (Jinja2) ← Service ← Use Case
```

## Зависимости

- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0** (async) — ORM
- **asyncpg** — драйвер PostgreSQL
- **Redis** — кэш, rate limiting, email-коды, JWT blacklist
- **Jinja2** — шаблоны
- **Pydantic** — настройки, DTO
