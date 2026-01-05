from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json

from .models import Feedback
from .forms import FeedbackForm, QuickFeedbackForm
from orders.models import Order


@require_POST
def submit_feedback(request):
    """Handle feedback submission via AJAX."""
    try:
        data = json.loads(request.body)
        
        # Get order if provided
        order = None
        order_id = data.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                pass
        
        # Create feedback
        feedback = Feedback(
            feedback_type=data.get('feedback_type', 'checkout_experience'),
            rating=data.get('rating'),
            subject=data.get('subject', ''),
            message=data.get('message', ''),
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            order=order,
        )
        
        # Link to user if authenticated
        if request.user.is_authenticated:
            feedback.user = request.user
            if not feedback.customer_name:
                feedback.customer_name = request.user.get_full_name()
            if not feedback.customer_email:
                feedback.customer_email = request.user.email
        
        feedback.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback! We appreciate you taking the time to share your experience.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


@require_POST
def submit_quick_feedback(request, order_id):
    """Handle quick feedback submission from order confirmation page."""
    order = get_object_or_404(Order, id=order_id)
    
    rating = request.POST.get('rating')
    message = request.POST.get('message', '')
    
    feedback = Feedback(
        order=order,
        feedback_type='checkout_experience',
        rating=int(rating) if rating else None,
        message=message,
    )
    
    if request.user.is_authenticated:
        feedback.user = request.user
        feedback.customer_name = request.user.get_full_name()
        feedback.customer_email = request.user.email
    else:
        feedback.customer_name = order.shipping_full_name
        feedback.customer_email = order.customer_email
    
    feedback.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
    
    messages.success(request, 'Thank you for your feedback!')
    return redirect('orders:order_confirmation', order_id=order.id)


def feedback_form_view(request):
    """Render feedback form page (standalone)."""
    if request.method == 'POST':
        form = FeedbackForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback! We appreciate your input.')
            return redirect('store:product_list')
    else:
        form = FeedbackForm(user=request.user if request.user.is_authenticated else None)
    
    return render(request, 'feedback/feedback_form.html', {'form': form})
