#!/bin/sh

# exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 "app.main:app"
