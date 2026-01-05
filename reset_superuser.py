import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscents.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

user, created = User.objects.get_or_create(username=username, defaults={'email': email})
user.email = email
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()

print(f"Superuser '{username}' has been reset/created with the provided credentials.")
