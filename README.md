# Документация проекта

## Обзор

Проект представляет собой веб-приложение для анализа URL с использованием FastAPI, Celery и Redis. Включает в себя:
- Backend сервис на FastAPI  
- Celery worker для асинхронных задач  
- Redis как брокер сообщений  
- Модель машинного обучения  
- Ollama для работы с LLM  
- Frontend интерфейс  

## Технологический стек

- **Backend**: FastAPI, Celery  
- **База данных**: SQLite
- **Брокер**: Redis  
- **ML модель**: Собственный сервис  
- **LLM**: Ollama с моделью llama3  
- **Frontend**: Vue3

## Запуск проекта

1. Убедитесь, что у вас установлены Docker и Docker Compose  
2. Клонируйте репозиторий
3. Запустите сервисы:  

```bash
docker compose up -d --build
```

### После запуска будут доступны:

1. Backend: http://localhost:8090
2. Frontend: http://localhost:8080
3. Модель: http://localhost:8050
4. Ollama: http://localhost:5252

### Конфигурация (.env)

1. BROKER_URL=redis://redis:6379/0
2. DATABASE_URL=sqlite:////data/database.db
3. MODEL_URL=http://model:8050

## Тестирование
Для запуска тестов с проверкой покрытия:

```bash
docker compose exec app pytest --cov=. --cov-report=term --cov-fail-under=75
```
Или для локального тестирования (после установки зависимостей):

```bash
pip install -r app/requirements.txt
pytest --cov=. --cov-report=term --cov-fail-under=75
```
