# Auth-service

```
docker compose -f docker-compose.dev.yml up auth-service
```

http://localhost:8008/

## docs

http://localhost:8008/api/openapi


## Миграции
### Создание
```
export STORAGE_DATABASE_HOST=localhost && export STORAGE_DATABASE_PORT=5434 && alembic revision --autogenerate -m "Initial"
```
### Применение
export STORAGE_DATABASE_HOST=localhost && export STORAGE_DATABASE_PORT=5434 && alembic upgrade head