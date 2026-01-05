"""Email utilities for sending transactional emails."""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_email(subject, template_name, context, to_email, from_email=None):
    """
    Send an email using a template.
    
    Args:
        subject: Email subject
        template_name: Path to the HTML template (without extension)
        context: Context dictionary for the template
        to_email: Recipient email address (string or list)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sceanicollections.com')
    
    if isinstance(to_email, str):
        to_email = [to_email]
    
    # Add common context
    context.update({
        'site_name': 'SceaniCollections',
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@sceanicollections.com'),
    })
    
    # Render templates
    html_content = render_to_string(f'emails/{template_name}.html', context)
    text_content = strip_tags(html_content)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_email
    )
    email.attach_alternative(html_content, 'text/html')
    
    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email to new user."""
    context = {
        'user': user,
        'user_name': user.get_full_name() or user.email.split('@')[0],
    }
    return send_email(
        subject='Welcome to SceaniCollections!',
        template_name='welcome',
        context=context,
        to_email=user.email
    )


def send_order_confirmation_email(order):
    """Send order confirmation email."""
    context = {
        'order': order,
        'user': order.user,
        'user_name': order.user.get_full_name() if order.user else order.shipping_full_name,
        'order_items': order.items.all(),
    }
    to_email = order.user.email if order.user else order.customer_email
    return send_email(
        subject=f'Order Confirmed - #{order.order_number}',
        template_name='order_confirmation',
        context=context,
        to_email=to_email
    )


def send_order_shipped_email(order):
    """Send shipping notification email."""
    context = {
        'order': order,
        'user': order.user,
        'user_name': order.user.get_full_name() if order.user else order.shipping_name,
        'tracking_number': order.tracking_number,
        'shipping_carrier': order.shipping_carrier,
    }
    to_email = order.user.email if order.user else order.email
    return send_email(
        subject=f'Your Order Has Shipped - #{order.order_number}',
        template_name='order_shipped',
        context=context,
        to_email=to_email
    )


def send_order_delivered_email(order):
    """Send delivery confirmation email."""
    context = {
        'order': order,
        'user': order.user,
        'user_name': order.user.get_full_name() if order.user else order.shipping_name,
    }
    to_email = order.user.email if order.user else order.email
    return send_email(
        subject=f'Your Order Has Been Delivered - #{order.order_number}',
        template_name='order_delivered',
        context=context,
        to_email=to_email
    )


def send_password_reset_email(user, reset_url):
    """Send password reset email."""
    context = {
        'user': user,
        'user_name': user.get_full_name() or user.email.split('@')[0],
        'reset_url': reset_url,
    }
    return send_email(
        subject='Reset Your Password - SceaniCollections',
        template_name='password_reset',
        context=context,
        to_email=user.email
    )


def send_newsletter_welcome_email(email, unsubscribe_token=None):
    """Send newsletter subscription confirmation."""
    context = {
        'email': email,
        'unsubscribe_token': unsubscribe_token,
    }
    return send_email(
        subject='Welcome to Our Newsletter!',
        template_name='newsletter_welcome',
        context=context,
        to_email=email
    )


def send_contact_form_email(name, email, subject, message):
    """Send contact form submission notification."""
    context = {
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
    }
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    return send_email(
        subject=f'Contact Form: {subject}',
        template_name='contact_form',
        context=context,
        to_email=admin_email
    )


def send_low_stock_alert(product):
    """Send low stock alert to admin."""
    context = {
        'product': product,
    }
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    return send_email(
        subject=f'Low Stock Alert: {product.name}',
        template_name='low_stock_alert',
        context=context,
        to_email=admin_email
    )
