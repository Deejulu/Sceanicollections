#!/bin/bash
# Render deploy hook: run migrations before starting the server
python manage.py migrate --noinput
exec gunicorn aniscents.wsgi:application
