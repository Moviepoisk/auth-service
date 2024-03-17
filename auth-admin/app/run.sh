#!/bin/sh

export FLASK_APP=${FLASK_APP:-app.app:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5001}

exec gunicorn --reload --bind $HOST:$PORT "$FLASK_APP"