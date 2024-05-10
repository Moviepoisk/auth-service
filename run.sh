#!/bin/sh

# exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"

alembic upgrade head
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 "app.main:app"
