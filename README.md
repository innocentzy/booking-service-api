# Booking Service API

RESTful API для управления бронированием недвижимости. Построен на FastAPI с асинхронным доступом к базе данных, очередью задач Celery и автоматической отправкой подтверждений по email с PDF-вложением.

## Стек технологий

| **Веб-фреймворк** | FastAPI |
| **База данных** | PostgreSQL (via `asyncpg`) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Миграции** | Alembic |
| **Очередь задач** | Celery + Redis |
| **Авторизация** | JWT (access + refresh tokens) |
| **Контейнеризация** | Docker Compose |
| **Тесты** | pytest + httpx (async) |

## Архитектура

```
┌─────────────┐     ┌───────────────┐     ┌──────────┐
│   Client    │────▶│  FastAPI App  │────▶│ PostgreSQL│
│             │◀────│  (uvicorn)    │◀────│          │
└─────────────┘     └───────┬───────┘     └──────────┘
                            │ отправляет задачи
                            ▼
                    ┌───────────────┐     ┌──────────┐
                    │ Celery Worker │────▶│  Redis   │
                    │               │◀────│ (broker) │
                    └───────────────┘     └──────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ SMTP (email)  │
                    │ + PDF gen     │
                    └───────────────┘
```

## Структура проекта

```
.
├── app/
│   ├── main.py            # Точка входа FastAPI
│   ├── config.py          # Настройки
│   ├── database.py        # Подключение к БД
│   ├── models.py          # SQLAlchemy ORM модели
│   ├── schemas.py         # Pydantic схемы
│   ├── crud.py            # Все операции с БД
│   ├── security.py        # Хеширование пароля и JWT
│   ├── dependencies.py    # FastAPI зависимости
│   ├── routes/
│   │   ├── auth.py        # Аутентификация
│   │   ├── properties.py  # Недвижимости
│   │   └── bookings.py    # Бронирования
│   └── worker/
│       ├── app.py         # Конфигурация Celery
│       └── tasks.py       # Генерация PDF + отправка email
```

## Быстрый старт

```
# Клонировать репозиторий
git clone https://github.com/innocentzy/booking-service-api.git
cd booking-service-api

# Создать .env файл
cp .env.example .env

# Запустить контейнеры
docker-compose up --build
```

API будет доступен по адресу: http://localhost:8000

Swagger UI: http://localhost:8000/docs

## API Endpoints

### Auth

| Method | Endpoint                | Описание                                |
| ------ | ----------------------- | --------------------------------------- |
| `POST` | `/auth/register/{role}` | Регистрация как `customer` или `host`   |
| `POST` | `/auth/login`           | Получение пары access + refresh токенов |
| `POST` | `/auth/update-token`    | Обновление access токена по refresh     |

### Properties

| Method   | Endpoint           | Описание                                                                   |
| -------- | ------------------ | -------------------------------------------------------------------------- |
| `GET`    | `/properties`      | Список с пагинацией и фильтрами (`city`, `beds`, `min_price`, `max_price`) |
| `GET`    | `/properties/{id}` | Детали недвижимости                                                        |
| `POST`   | `/properties`      | Создание недвижимости _(host/admin)_                                       |
| `PATCH`  | `/properties/{id}` | Частичное обновление _(host/admin)_                                        |
| `DELETE` | `/properties/{id}` | Удаление недвижимости _(host/admin)_                                       |

### Bookings

| Method   | Endpoint         | Описание                                  |
| -------- | ---------------- | ----------------------------------------- |
| `GET`    | `/bookings`      | Список бронирований текущего пользователя |
| `GET`    | `/bookings/{id}` | Детали бронирования _(customer/host)_     |
| `POST`   | `/bookings`      | Создание бронирования _(customer)_        |
| `DELETE` | `/bookings/{id}` | Отмена бронирования _(customer/admin)_    |

## Ключевые решения

**Async по умолчанию.** Приложение FastAPI и все обращения к БД работают через async-движок SQLAlchemy. Отдельная sync-фабрика сессий создана специально для Celery-воркера, поскольку задачи Celery выполняются в синхронном контексте.

**Row-level lock для бронирований.** `create_booking` захватывает блокировку `SELECT ... FOR UPDATE` на строке property. Это исключает ситуацию двойного бронирования при конкурентных запросах.

**Celery chain для уведомлений.** Генерация PDF и отправка email реализованы как две отдельные задачи в цепочке, а не единый монолитный таск. Это позволяет каждому шагу быть независимо повторяемым.

## Тестирование

Тесты используют in-memory SQLite.

```bash
# Установить зависимости для тестов
pip install -r requirements.txt

# Запустить тесты
pytest
```

## Переменные окружения

### База данных

| Переменная          | Описание                     | По умолчанию                                                    |
| ------------------- | ---------------------------- | --------------------------------------------------------------- |
| `DATABASE_URL`      | URL подключения к PostgreSQL | `postgresql+asyncpg://postgres:postgres@db:5432/bookingservice` |
| `POSTGRES_USER`     | Пользователь PostgreSQL      | `postgres`                                                      |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL            | `postgres`                                                      |
| `POSTGRES_DB`       | Имя базы данных              | `bookingservice`                                                |

> `POSTGRES_USER`, `POSTGRES_PASSWORD` и `POSTGRES_DB` должны соответствовать тому, что указано в `DATABASE_URL`.

### JWT и авторизация

| Переменная                    | Описание                           | По умолчанию      |
| ----------------------------- | ---------------------------------- | ----------------- |
| `SECRET_KEY`                  | Секретный ключ для JWT             | `your-secret-key` |
| `ALGORITHM`                   | Алгоритм подписи JWT               | `HS256`           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access токена (минуты) | `30`              |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Время жизни refresh токена (дни)   | `7`               |

### Redis и Celery

| Переменная              | Описание                  | По умолчанию           |
| ----------------------- | ------------------------- | ---------------------- |
| `REDIS_URL`             | URL Redis                 | `redis://redis:6379/0` |
| `CELERY_BROKER_URL`     | URL Брокера Celery        | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Бэкенд результатов Celery | `redis://redis:6379/0` |

### SMTP

| Переменная        | Описание                                                   | По умолчанию           |
| ----------------- | ---------------------------------------------------------- | ---------------------- |
| `SMTP_HOST`       | Хост почтового сервера                                     | `smtp.gmail.com`       |
| `SMTP_PORT`       | Порт SMTP                                                  | `587`                  |
| `SMTP_USER`       | Логин SMTP                                                 | `your-email@gmail.com` |
| `SMTP_PASSWORD`   | Пароль SMTP (для Gmail — App Password, не пароль аккаунта) | `your-app-password`    |
| `EMAIL_FROM`      | Адрес отправителя                                          | `your-email@gmail.com` |
| `EMAIL_FROM_NAME` | Имя отправителя в письме                                   | `Booking Service`      |

## Миграции

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```
