# TaskFlow

> Backend для TodoList веб-приложения. 

#### Используется:

- FastAPI — основной фреймворк для разработки с поддержкой асинхронных REST API и встроенной документацией.
- SQLAlchemy — объектно-реляционное отображение (ORM) для работы с базой данных PostgreSQL.
- Alembic — инструмент миграций для SQLAlchemy, используемый для управления схемой базы данных.
- PostgreSQL — основная реляционная база данных проекта.
   - uuid-ossp - расширение для генерации uuid-v4
- Redis — используется для хранения refresh-токенов и реализации ограничения количества запросов (rate limiting).
- MinIO — локальное S3-совместимое файловое хранилище, применяемое для загрузки и хранения пользовательских файлов и изображений.
- Pydantic — библиотека для строгой валидации и сериализации данных, используемая при описании входных и выходных схем FastAPI.


## Запуск проекта
1. **Клонировать репозиторий**
   ```shell
   git clone <URL>
   ```

2. **Установить Docker и Docker Compose**
   - Для Windows или macOS: https://www.docker.com/products/docker-desktop
   - Для Linux:
      - Установка Docker: https://docs.docker.com/engine/install/
      - Установка Docker Compose: https://docs.docker.com/compose/install/

3. **Конфигурация окружения**
   - Настроить`.env` в корне проекта, пример: [.env.example](.env.example)
   - Настроить `redis.conf`Ж ([redis.conf.example](redis.conf.example)):
   
   > Пароль для Redis в `.env` и `redis.conf` должен совпадать
   
4. **Запуск проекта**
   В корневой папке проекта (где находится docker-compose.yml):
   ```shell
   docker-compose up --build
   ```
   
5. **Доступ к приложению**
   После запуска приложение будет доступно по адресу, указанному в конфигурации (обычно http://localhost:8000).


## Разработка

1. **Установка UV**
   https://github.com/astral-sh/uv?tab=readme-ov-file#installation
   > UV - пакетный менеджер для Python
   
2. **Создание виртуального окружения**
   ```shell
   uv venv --python 3.13.5
   ```

3. **Установка зависимостей из pyproject.toml**
   ```shell
   uv install -r pyproject.toml
   ```
   
4. **Установка зависимостей для разработки (опционально)**
   Если планируется использовать такие инструменты, как ruff, mypy, pytest и т.п.:
   ```shell
   uv pip install -r requirements-dev.txt
   ```
## Миграции

#### Создать Миграцию

```shell
alembic revision --autogenerate -m "<MSG>"
```

#### Применить миграцию

```shell
alembic upgrade head
```