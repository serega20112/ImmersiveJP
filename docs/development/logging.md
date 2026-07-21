# Логирование

## Формат

Приложение пишет логи в `stdout` в JSON-формате. Каждая запись содержит:

| Поле | Описание |
|------|----------|
| `timestamp` | ISO-8601 с миллисекундами |
| `level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `logger` | Имя логгера (обычно `__name__`) |
| `message` | Текст сообщения |
| `event` | Имя события (опционально) |
| `extra_fields` | Дополнительные поля: `request_id`, `user_id`, `path`, `track`, `batch_number`, `duration_ms` |
| `exception` | Stacktrace при ошибке (опционально) |

Пример строки лога:

```json
{"timestamp":"2026-07-21T12:34:56.789Z","level":"INFO","logger":"src.backend.infrastructure.web.middleware","message":"HTTP request completed","event":"request_completed","duration_ms":342,"method":"GET","path":"/learn/language","status_code":200}
```

## Что логируется

- Все входящие HTTP-запросы и их длительность (middleware).
- Необработанные ошибки и HTTP/validation ошибки.
- Cache hit/miss для LLM.
- Попытки обращения к LLM и переход на fallback при проблемах внешней модели.
- Ключевые действия пользователя:
  - завершение онбординга
  - генерация партии карточек
  - генерация речевой практики
  - отправка работы на проверку

## Как использовать

```python
from src.backend.infrastructure.observability import get_logger, log_event

logger = get_logger(__name__)
logger.info("Сообщение")
log_event(logger, logging.INFO, "cards_generated", "Сгенерировано 5 карточек", user_id=42, track="language")
```

## Настройки

Через `.env`:

| Переменная | Описание |
|------------|----------|
| `LOG_LEVEL` | Уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ELASTICSEARCH_ENABLED` | Отправлять логи в Elasticsearch (`true`/`false`) |
| `ELASTICSEARCH_URL` | URL Elasticsearch (ex. `http://localhost:9200`) |
| `ELASTICSEARCH_LOG_INDEX` | Индекс Elasticsearch (по умолчанию `immersjp-logs`) |

Если `ELASTICSEARCH_ENABLED=true`, к корневому логгеру добавляется `ElasticsearchLogHandler`, который асинхронно (fire-and-forget) отправляет каждую запись в Elasticsearch.

## Просмотр логов

Локально — `stdout`. В Docker Compose подключен Dozzle.

```powershell
docker compose up --build
```

Веб-интерфейс: `http://localhost:8081`

Dozzle показывает логи контейнеров вживую. JSON уже структурирован — позже его можно направлять в Elastic/Kibana, Loki или любой другой агрегатор.
