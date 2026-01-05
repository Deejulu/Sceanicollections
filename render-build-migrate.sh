#!/bin/bash
# Render deploy hook: run migrations before starting the server
python manage.py migrate --noinput
python manage.py sync_admin_password
exec gunicorn aniscents.wsgi:application
