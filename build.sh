
#!/usr/bin/env bash
set -o errexit

echo "=== 1. Installing dependencies ==="
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "=== 2. Running database migrations ==="
python manage.py migrate

echo "=== 3. Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== 4. Build complete ==="
