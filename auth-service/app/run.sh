#!/bin/sh

export APP_MODULE=${APP_MODULE-app.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

# exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 "$APP_MODULE"