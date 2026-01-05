pip install -r requirements.txt

#!/usr/bin/env bash
set -o errexit

# Upgrade pip, setuptools, and wheel for Python 3.13 compatibility
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python manage.py migrate

# Create superuser if not exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(username=username).exists():
	User.objects.create_superuser(username, email, password)
	print(f'Superuser {username} created')
else:
	print(f'Superuser {username} already exists')
"
python manage.py collectstatic --noinput
