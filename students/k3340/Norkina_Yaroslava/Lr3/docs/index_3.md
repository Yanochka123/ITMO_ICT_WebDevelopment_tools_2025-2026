# Лабораторная работа №3: Упаковка FastAPI приложения в Docker, Работа с источниками данных и Очереди


Была создана БД для программы тайм-менеджера, согласно описанию в варианте. На основе предоставленных данных о функционале был создан код для запуска проекта тайм-менеджмента через файл main.py с временной БД и API эндпоинтами, аналогично практике 1.

Цель: научиться упаковывать FastAPI приложение в Docker, интегрировать парсер данных с базой данных и вызывать парсер через API и очередь.

## Термины

Контейнер — текущий экземпляр, который инкапсулирует необходимое ПО. Контейнеры всегда создаются из образов. Могут открывать порты и тома для взаимодействия с другими контейнерами и/или внешним миром, а также легко удаляются и пересоздаются заново за короткий промежуток времени.  

Образ — основной элемент для каждого контейнера. После его создания каждый шаг кэшируется и может быть использован повторно (модель копирования при записи). В зависимости от образа может понадобиться некоторое время для его построения. Из них могут быть сразу запущены контейнеры.  

Порт — TCP/UDP-порт в своем обычном представлении. Порты могут быть открыты для внешнего мира (доступы через основную ОС) или подсоединены к другим контейнерам — доступны только из тех контейнеров и невидимы для внешнего мира.  

Образ контейнера можно сравнить с файлами программы, например python и каким-то файлом main.py.
А сам контейнер (в отличие от образа контейнера) — это фактически запущенный экземпляр образа, сопоставимый с процессом. По сути, контейнер работает только тогда, когда в нём есть запущенный процесс (и обычно это один процесс). Контейнер останавливается, когда в нём не остаётся запущенных процессов.  

Том — может быть описан как общая папка. Тома инициализируются при создании контейнера. Они спроектированы для хранения данных независимо от жизненного цикла контейнера.  

Реестр — сервер, который хранит образы Docker. Функционирует по аналогии с Github — можно вытянуть образ, чтобы развернуть его локально, а затем закинуть обратно в реестр.  
Docker Hub — реестр с веб-интерфейсом, созданный Docker Inc. Он хранит большое количество Docker-образов с разным ПО. Docker Hub является источником «официальных» Docker-образов, созданных командой Docker. Официальные образы содержат списки своих потенциальных уязвимостей. Эта информация доступна для каждого авторизированного пользователя. Доступны два типа аккаунтов: бесплатные и платные. На бесплатном аккаунте может быть один приватный образ и бесконечное количество общедоступных образов.

Команда для создания образа:  
docker build . -t test-curl

docker bulid — создает новый локальный образ.
-t — устанавливает именную метку для образа.

Стайлгайды Docker  

	• 1 приложение = 1 контейнер.
	• Запускайте процесс на переднем плане (не используйте systemd, upstart или другие похожие инструменты).
	• Для хранения данных вне контейнера используйте тома.
	• Не иcпользуйте SSH (если вам надо залезть внутрь контейнера, используйте docker exec).
	• Избегайте ручных настроек или действий внутри контейнера.
	• Включайте только необходимый контекст — используйте .dockerignore файл (как .gitignore в git).
	• Избегайте установки ненужных пакетов — это займет лишнее дисковое пространство.
	• Используйте кэш. Добавьте контекст, который часто меняется, например, исходный код вашего проекта, в конец Dockerfile — кэш Docker будет использоваться более эффективно.
	• Будьте осторожны с томами. Вы должны помнить, какие данные находятся в томах. Поскольку тома постоянны и не исчезают вместе с контейнерами, следующий контейнер будет использовать данные, которые были созданы предыдущим контейнером.
	• Используйте переменные окружения: RUN, EXPOSE, VOLUME. Это сделает ваш Dockerfile более гибким.


Healthcheck -  Проверка состояния/работоспособности. Основная задача healthcheck’а – как можно скорее уведомить среду, управляющую контейнером, о том, что с контейнером что-то не так. И самая простая стратегия решения проблемы – перезапуск контейнера.
Так же стоит сразу позаботиться об ограничении ресурсов для контейнера с БД. Для экспериментов и локального запуска вполне подойдёт секция resources.

В современной разработке любой микросервис или инфраструктурный компонент должен быть поставлен на мониторинг, то есть непрерывно отдавать метрики - ключевые показатели, позволяющие определить, как ведёт себя система в данный момент времени.
PostgreSQL не имеет встроенной интеграции с системами мониторинга наподобие Prometheus (или Zabbix). Вместо этого он полагает


## Использованные технологии


| Технология	    | Назначение                                     |
|------------------ | ---------------------------------------------- |
| Docker	        | упаковка приложений в контейнеры
| Docker Compose	| запуск нескольких сервисов одной командой
| FastAPI	        |основное API и API сервиса парсера
| PostgreSQL	    | общая база данных
|  Redis	        | брокер сообщений для очереди задач
| Celery	        | фоновая обработка задач парсинга
| requests  	    | HTTP-запросы между сервисами и загрузка страниц
|  BeautifulSoup	| извлечение заголовка HTML-страницы
|  Alembic	        | применение миграций базы данных


## Сервисы Docker Compose
В docker-compose.yml описаны следующие сервисы:


### Таблица сервисов проекта

| Сервис | Назначение | Порт (host:container) | URL |
|---|---|---|---|
| **tm_postgres** | PostgreSQL 16 — база данных проекта | `5432:5432` | — |
| **tm_api** | FastAPI тайм-менеджер: CRUD задач, категорий, тегов, JWT-авторизация, фронтенд, проксирование запросов к парсеру | `8000:8000` | http://localhost:8000 |
| **tm_parser** | FastAPI-обёртка парсера: приём URL, парсинг HTML, сохранение `<title>` и метаданных в БД от имени пользователя `parser` | `8001:8001` | http://localhost:8001 |

## Порты для подключения извне

| Что | Адрес |
|---|---|
| Фронтенд / API | http://localhost:8000 |
| Swagger API | http://localhost:8000/docs |
| Swagger Parser | http://localhost:8001/docs |
| PostgreSQL (psql, DBeaver) | `localhost:5432` |
| Parser напрямую | http://localhost:8001 |

## Подзадача 1. Упаковка в Docker
Были созданы Dockerfile для:

основного FastAPI-приложения;
сервиса парсера;
Celery worker.
Также был создан общий docker-compose.yml, который запускает все необходимые сервисы одной командой:

docker compose up --build
При запуске основного приложения автоматически выполняются миграции Alembic.

Docker-compose.yml:
``` Bash
# time-manager-app/docker-compose.yml
version: "3.9"

services:
  # ============================================================
  # PostgreSQL
  # ============================================================
  postgres:
    image: postgres:16-alpine
    container_name: tm_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - tm_network

  # ============================================================
  # FastAPI (тайм-менеджер)
  # ============================================================
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: tm_api
    restart: unless-stopped
    environment:
      # Внутри контейнера DB_HOST=postgres (имя сервиса)
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${POSTGRES_DB}
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      ALGORITHM: ${ALGORITHM}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - tm_network

  # ============================================================
  # Parser (FastAPI-обёртка)
  # ============================================================
  parser:
    build:
      context: .
      dockerfile: Dockerfile.parser
    container_name: tm_parser
    restart: unless-stopped
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${POSTGRES_DB}
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - tm_network

volumes:
  postgres_data:

networks:
  tm_network:
    driver: bridge
```

### Ключевые моменты:

DB_HOST: postgres — жёстко прописан для контейнеров api и parser. Это перекрывает значение из app/.env (localhost), потому что Docker передаёт переменные через environment, и os.getenv("DB_HOST") вернёт postgres.

${POSTGRES_USER} и т.д. — подставляются из time-manager-app/.env (Docker Compose читает .env из текущей директории автоматически).

postgres_data — именованный volume, чтобы данные БД сохранялись между перезапусками.

depends_on: condition: service_healthy — api и parser ждут, пока postgres реально станет доступен.


## Подзадача 2. Вызов парсера из FastAPI по HTTP

### Запуск

Команды для запуска:
``` Bash
# Собрать и запустить
docker compose up --build

# Или в фоне
docker compose up -d --build

# Логи
docker compose logs -f api
docker compose logs -f parser

# Остановить
docker compose down

# Остановить и удалить данные БД
docker compose down -v
```




docker compose up --build
<img width="1328" height="467" alt="image" src="https://github.com/user-attachments/assets/c29d837b-4ba7-4cca-b055-2b4c623e0ddf" />

Docker Compose читает time-manager-app/.env:

text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=135papin
POSTGRES_DB=time_management_db
SECRET_KEY=135papin
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DB_HOST=postgres
...
Запускает контейнер postgres с POSTGRES_* — создаётся БД time_management_db с пользователем postgres и паролем 135papin.

Запускает контейнер api с environment:

text
DB_HOST=postgres
DB_PORT=5432
DB_NAME=time_management_db
DB_USER=postgres
DB_PASSWORD=135papin
SECRET_KEY=135papin
...
Внутри api load_dotenv() ничего не находит (.env не скопирован), и os.getenv("DB_HOST") возвращает postgres из environment.

app/database.py строит DSN:

text
postgresql://postgres:135papin@postgres:5432/time_management_db
Docker DNS резолвит postgres в IP контейнера postgres.

Подключение работает.
<img width="1486" height="308" alt="image" src="https://github.com/user-attachments/assets/ca75a287-8b0c-4bb9-bc5b-688b37a00432" />

Теперь можно добавить эндпоинт для вызова парсера
Раз оба контейнера работают и в одной Docker-сети, api может обращаться к parser по имени parser:8001. Добавим интеграцию.
Добавлен новый маршрут в app/routes/parser.py:
``` Python
# app/routes/parser.py
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from app import schemas, models
from app.routes.auth import get_current_user

router = APIRouter(prefix="/parser", tags=["parser"])

PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")


@router.post("/parse", response_model=schemas.ParseUrlResponse)
async def parse_url(
    payload: schemas.ParseUrlRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Проксирует запрос к сервису парсера."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{PARSER_URL}/parse",
                json={"url": payload.url, "save_to_db": payload.save_to_db},
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        return response.json()
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Parser service unavailable: {e}",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Parser service timed out",
        )


@router.get("/health")
async def parser_health():
    """Проверяет доступность парсера из API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PARSER_URL}/health")
        return {
            "parser_url": PARSER_URL,
            "status_code": response.status_code,
            "body": response.json(),
        }
    except httpx.HTTPError as e:
        return {
            "parser_url": PARSER_URL,
            "status": "unavailable",
            "error": str(e),
        }
```

### Проверка

Проверка
1. Контейнеры запущены
powershell
docker compose ps
Должны быть три контейнера со статусом Up (healthy).
<img width="1697" height="444" alt="image" src="https://github.com/user-attachments/assets/98c5c140-4372-453f-939f-0a584655ac5d" />


Команды, чтобы пересобрать api:
docker compose build --no-cache api

Команда для запуска контейнера и результат:
docker compose up -d

<img width="1703" height="317" alt="image" src="https://github.com/user-attachments/assets/a59fcc93-1652-49ce-95c5-c15b7c33579d" />
<img width="1690" height="283" alt="image" src="https://github.com/user-attachments/assets/d726b917-0054-4b0d-b0ff-fcfd08942625" />


3. Логи api
powershell
docker compose logs api
Должно быть что-то вроде:

text
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
Никаких fe_sendauth: no password supplied.

3. Логи parser
powershell
docker compose logs parser
Должно быть:

text
[Конфиг] .env не найден — используются переменные окружения
Подключение к БД: postgresql://postgres:****@postgres:5432/time_management_db
Обратите внимание: @postgres:5432, а не @localhost:5432.

4. Проверка изнутри контейнера
powershell
docker compose exec api python -c "import os; print(os.getenv('DB_HOST'))"
Должно вывести postgres.

5. Проверка API
powershell
curl http://localhost:8000/health
curl http://localhost:8001/health

<img width="1859" height="890" alt="image" src="https://github.com/user-attachments/assets/f27fc20b-06a5-4136-b0e5-1f9664f32597" />

7. Проверка БД
powershell
docker compose exec postgres psql -U postgres -d time_management_db -c "\dt"
<img width="665" height="474" alt="image" src="https://github.com/user-attachments/assets/b04e02a8-b769-46b0-97f4-c4e5f7a25435" />


8. Проверка парсера
```
# Логин
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user@example.com&password=yourpassword"

# Парсинг (подставьте токен)
curl -X POST http://localhost:8000/parser/parse `
  -H "Authorization: Bearer <access_token>" `
  -H "Content-Type: application/json" `
  -d '{\"url\": \"https://example.com\", \"save_to_db\": true}'
```
Результат:
<img width="1804" height="655" alt="image" src="https://github.com/user-attachments/assets/50084d54-0c80-4aee-81e5-6db8933f3f00" />
<img width="1762" height="852" alt="image" src="https://github.com/user-attachments/assets/b61e0d35-8bf2-4115-b425-66926c0a73b3" />

Данные корректно сохраняются в БД:
<img width="1709" height="230" alt="image" src="https://github.com/user-attachments/assets/2a482f2f-b8f2-4845-bca6-ac477dfd9e5f" />

Проверка созданных тегов:
docker compose exec postgres psql -U postgres -d time_management_db -c "SELECT id, name, user_id FROM tags WHERE user_id = (SELECT id FROM users WHERE username='parser') LIMIT 10;"
<img width="1708" height="238" alt="image" src="https://github.com/user-attachments/assets/b8af6fe4-b3ea-4615-8855-662cc840d795" />

## Вывод
В третьей лабораторной работе FastAPI-приложение, база данных, парсер были упакованы в Docker Compose. Основное приложение может вызывать парсер напрямую по HTTP или ставить задачу парсинга в очередь. Все сервисы используют одну общую PostgreSQL-базу данных, что соответствует замечанию о недопустимости создания отдельной базы для каждого микросервиса.
