#!/bin/sh
set -e

echo "⏳ Waiting for Postgres..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done
echo "✅ Postgres is up."

echo "⏳ Waiting for Qdrant..."
until python -c "import urllib.request; urllib.request.urlopen('${QDRANT_URL}/healthz')" 2>/dev/null; do
  sleep 0.5
done
echo "✅ Qdrant is up."

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --timeout 600