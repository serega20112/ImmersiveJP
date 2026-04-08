# Логирование

## Формат

Приложение пишет логи в `stdout` в JSON-формате. Каждая запись содержит:

- `timestamp`
- `level`
- `logger`
- `message`
- `event`
- дополнительные поля события: `request_id`, `user_id`, `path`, `track`, `batch_number`, `duration_ms`

## Что логируется

- входящие HTTP-запросы и их длительность
- необработанные ошибки и HTTP/validation ошибки
- cache hit/miss для LLM
- попытки обращения к LLM
- переход на fallback при проблемах внешней модели
- ключевые действия пользователя:
  - завершение онбординга
  - генерация партии карточек
  - генерация речевой практики
  - отправка работы

## Настройки

Через `.env`:

- `LOG_LEVEL=INFO`
- `HF_TIMEOUT_SECONDS=12`
- `HF_RETRY_ATTEMPTS=3`
- `HF_RETRY_BACKOFF_SECONDS=0.8`
- `TEXT_INPUT_LIMIT=500`

## Просмотр логов

В `docker-compose` подключен `Dozzle`.

Запуск:

```powershell
docker compose -f build/docker-compose.yml up --build
```

Веб-интерфейс:

- `http://localhost:8081`

Dozzle показывает логи контейнеров вживую. JSON уже структурирован, поэтому позже его можно без переделки направить в `Elastic/Kibana`, `Loki` или другой агрегатор.
