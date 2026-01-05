# Use official Python 3.12 image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
	&& pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files (optional, if you want to do it at build time)
# RUN python manage.py collectstatic --noinput

# Default command (can be overridden by Render Start Command)
CMD ["gunicorn", "store.wsgi:application", "--bind", "0.0.0.0:8000"]
