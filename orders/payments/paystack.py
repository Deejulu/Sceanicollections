import requests
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from orders.models import Order

def initiate_paystack_payment(request, order_id):
	order = get_object_or_404(Order, id=order_id, user=request.user)
    
	# Paystack integration
	paystack_secret_key = settings.PAYSTACK_SECRET_KEY
    
	# Create Paystack transaction
	headers = {
		'Authorization': f'Bearer {paystack_secret_key}',
		'Content-Type': 'application/json',
	}
    
	data = {
		'email': order.customer_email,
		'amount': int(order.total * 100),  # Convert to kobo
		'reference': order.order_number,
		'callback_url': request.build_absolute_uri(reverse('orders:payment_callback')),
		'metadata': {
			'order_id': order.id,
			'customer_id': request.user.id if request.user.is_authenticated else None,
		}
	}
    
	response = requests.post('https://api.paystack.co/transaction/initialize', 
						   headers=headers, 
						   json=data)
    
	if response.status_code == 200:
		payment_data = response.json()
		return redirect(payment_data['data']['authorization_url'])
    
	messages.error(request, "Payment initiation failed. Please try again.")
	return redirect('orders:checkout')
