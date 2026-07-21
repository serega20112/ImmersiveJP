# Схема базы данных

PostgreSQL + Alembic для миграций. Redis используется отдельно для кэша и временных данных.

---

## Таблицы PostgreSQL

### `users`

Основная таблица пользователей.

| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| `id` | `INTEGER` | PK | |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | Email пользователя |
| `password_hash` | `VARCHAR(255)` | NOT NULL | bcrypt-хэш пароля |
| `display_name` | `VARCHAR(120)` | NOT NULL | Отображаемое имя |
| `is_email_verified` | `BOOLEAN` | NOT NULL, DEFAULT false | Флаг подтверждения почты |
| `learning_goal` | `VARCHAR(32)` | NULLABLE | Цель обучения (ex. `daily`, `weekly`) |
| `language_level` | `VARCHAR(32)` | NULLABLE | Уровень языка (ex. `beginner`, `intermediate`) |
| `study_timeline` | `VARCHAR(32)` | NULLABLE | Интенсивность (ex. `3_months`, `6_months`) |
| `interests_json` | `JSON` | NOT NULL, DEFAULT `[]` | Список интересов |
| `onboarding_completed` | `BOOLEAN` | NOT NULL, DEFAULT false | Онбординг пройден |
| `diagnostic_score` | `INTEGER` | NULLABLE | Балл диагностики |
| `diagnostic_level` | `VARCHAR(32)` | NULLABLE | Уровень по диагностике |
| `diagnostic_summary` | `TEXT` | NULLABLE | Сводка диагностики |
| `strengths_json` | `JSON` | NULLABLE | Сильные стороны |
| `weak_points_json` | `JSON` | NULLABLE | Слабые места |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | From `TimestampMixin` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | From `TimestampMixin` |

### `learning_cards`

Сгенерированные ИИ карточки-конспекты.

| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| `id` | `INTEGER` | PK | |
| `user_id` | `INTEGER` | FK → users(id) ON DELETE CASCADE, INDEX | |
| `track` | `VARCHAR(32)` | NOT NULL, INDEX | Трек: `language`, `culture`, `history` |
| `topic` | `VARCHAR(255)` | NOT NULL | Тема карточки |
| `explanation` | `TEXT` | NOT NULL | Основное объяснение |
| `examples_json` | `JSON` | NOT NULL, DEFAULT `[]` | Примеры использования |
| `key_terms_json` | `JSON` | NOT NULL, DEFAULT `[]` | Ключевые термины |
| `batch_number` | `INTEGER` | NOT NULL, DEFAULT 1 | Номер партии |
| `position` | `INTEGER` | NOT NULL | Позиция внутри партии |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | |

**Уникальность:** `(user_id, track, batch_number, position)` — гарантирует, что у пользователя в одном треке в одной партии нет дубликатов по позиции.

### `card_completions`

Отмечает пройденные пользователем карточки.

| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| `id` | `INTEGER` | PK | |
| `user_id` | `INTEGER` | FK → users(id) ON DELETE CASCADE, INDEX | |
| `card_id` | `INTEGER` | FK → learning_cards(id) ON DELETE CASCADE, INDEX | |
| `completed_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | Время завершения |

**Уникальность:** `(user_id, card_id)` — пользователь не может пройти одну карточку дважды.

### `learning_sessions`

Текущее состояние обучения пользователя по каждому треку.

| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| `id` | `INTEGER` | PK | |
| `user_id` | `INTEGER` | FK → users(id) ON DELETE CASCADE, INDEX | |
| `track` | `VARCHAR(32)` | NOT NULL, INDEX | Трек |
| `last_generated_batch` | `INTEGER` | NOT NULL, DEFAULT 0 | Номер последней сгенерированной партии |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | |

**Уникальность:** `(user_id, track)` — одна запись на пользователя на трек.

### `user_documents`

Пользовательские конспекты и заметки.

| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| `id` | `INTEGER` | PK, INDEX | |
| `user_id` | `INTEGER` | FK → users(id), NOT NULL | |
| `title` | `VARCHAR(255)` | NOT NULL | Заголовок |
| `content` | `TEXT` | NOT NULL | Текстовое содержимое |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT now() | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | From `TimestampMixin` |

---

## Связи

```
users (1) ──── (N) learning_cards
users (1) ──── (N) card_completions ──── (1) learning_cards
users (1) ──── (N) learning_sessions
users (1) ──── (N) user_documents
```

`card_completions` — ассоциативная таблица со временем завершения.

---

## Redis

Redis не является постоянным хранилищем и используется для:

- **Кэш ответов LLM** — ключ по хэшу запроса, TTL настраиваемый.
- **Rate limiting** — счётчики запросов с expiry-окном.
- **Коды подтверждения email** — TTL 20 минут.
- **Blacklist JWT** — отозванные токены до истечения срока.

Настройки Redis: `REDIS_URL` в `.env`, по умолчанию `redis://localhost:6379/0`.

Redis опционален (флаг `REDIS_REQUIRED=false`). Если Redis недоступен, приложение работает без кэша и rate limiting-а.

---

## Миграции

Управляются через Alembic.

```powershell
# Создать новую миграцию
alembic -c build/alembic/alembic.ini revision --autogenerate -m "описание"

# Применить миграции
alembic -c build/alembic/alembic.ini upgrade head

# Откатить
alembic -c build/alembic/alembic.ini downgrade -1
```

Все изменения схемы — только через ревизии, `create_all` не используется.
