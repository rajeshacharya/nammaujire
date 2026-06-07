#!/usr/bin/env bash
set -o errexit

mkdir -p "$(dirname "${SQLITE_PATH:-db.sqlite3}")"
mkdir -p "${MEDIA_ROOT:-media}"

if [ -n "$SQLITE_PATH" ] && [ ! -f "$SQLITE_PATH" ] && [ -f "db.sqlite3" ]; then
  cp db.sqlite3 "$SQLITE_PATH"
fi

if [ -n "$MEDIA_ROOT" ] && [ "$MEDIA_ROOT" != "media" ] && [ -d "media" ]; then
  cp -n -R media/. "$MEDIA_ROOT/" 2>/dev/null || true
fi

python manage.py migrate --no-input
gunicorn nammaujire.wsgi:application --bind "0.0.0.0:${PORT:-10000}"
