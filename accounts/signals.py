"""Signal handlers for account-related events."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_created_handler(sender, instance, created, **kwargs):
    """Send welcome email when user is created."""
    if created and instance.email:
        from accounts.utils import send_welcome_email
        send_welcome_email(instance)
