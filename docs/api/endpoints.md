# API и маршруты

Публичные страницы:

- `GET /` — лендинг
- `GET /auth/register` — форма регистрации
- `GET /auth/login` — форма входа
- `GET /auth/verify-email` — форма подтверждения почты

Аутентификация:

- `POST /auth/register` — создает пользователя и отправляет код
- `POST /auth/login` — выдает JWT в cookie
- `POST /auth/logout` — отзывает токены и чистит cookie
- `POST /auth/verify-email` — подтверждает почту

Основной маршрут обучения:

- `GET /onboarding`
- `POST /onboarding`
- `GET /dashboard`
- `GET /learn/language`
- `GET /learn/culture`
- `GET /learn/history`
- `POST /learn/complete`
- `GET /learn/next?track=...`
- `GET /learn/download-pdf?track=...`
- `GET /profile`

Все защищенные страницы читают текущего пользователя из JWT cookie через middleware и `ResolveCurrentUserUseCase`.
