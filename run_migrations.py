import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscents.settings')
django.setup()

from django.core.management import execute_from_command_line

execute_from_command_line(['manage.py', 'migrate'])
