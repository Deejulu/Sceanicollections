import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Syncs the Django admin password with DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD environment variables.'

    def handle(self, *args, **options):
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not admin_password:
            self.stdout.write(self.style.WARNING('DJANGO_SUPERUSER_PASSWORD environment variable not set. Skipping admin password sync.'))
            return
        User = get_user_model()
        try:
            user = User.objects.get(email=admin_email)
            user.set_password(admin_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Admin password updated for {admin_email}'))
        except User.DoesNotExist:
            User.objects.create_superuser(email=admin_email, password=admin_password)
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin_email}'))
