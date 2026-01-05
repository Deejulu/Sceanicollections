"""Signal handlers for order-related events."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def order_created_handler(sender, instance, created, **kwargs):
    """Send order confirmation email when order is created."""
    if created:
        from accounts.utils import send_order_confirmation_email
        send_order_confirmation_email(instance)


@receiver(pre_save, sender=Order)
def order_status_changed_handler(sender, instance, **kwargs):
    """Send emails when order status changes."""
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            
            # Check if status changed to shipped
            if old_order.status != 'shipped' and instance.status == 'shipped':
                from accounts.utils import send_order_shipped_email
                send_order_shipped_email(instance)
            
            # Check if status changed to delivered
            if old_order.status != 'delivered' and instance.status == 'delivered':
                from accounts.utils import send_order_delivered_email
                send_order_delivered_email(instance)
        except Order.DoesNotExist:
            pass
