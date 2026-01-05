from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import uuid

from .models import Order, OrderItem
from .forms import CheckoutForm
from cart.cart import get_cart, clear_cart


def checkout(request):
    """Handle checkout process"""
    cart = get_cart(request)
    
    # Check if cart is empty
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty. Please add items before checkout.')
        return redirect('cart:detail')
    
    cart_items = cart.items.select_related('product', 'variant').all()
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Create order
            order = Order(
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                customer_email=form.cleaned_data['email'],
                customer_phone=form.cleaned_data['phone'],
                
                # Shipping address
                shipping_full_name=form.cleaned_data['full_name'],
                shipping_address=form.cleaned_data['address'],
                shipping_city=form.cleaned_data['city'],
                shipping_state=form.cleaned_data['state'],
                shipping_postal_code=form.cleaned_data.get('postal_code', ''),
                shipping_country=form.cleaned_data['country'],
                shipping_phone=form.cleaned_data['phone'],
                
                # Payment & Shipping method
                payment_method=form.cleaned_data['payment_method'],
                shipping_method=form.cleaned_data['shipping_method'],
                
                # Order notes
                customer_notes=form.cleaned_data.get('notes', ''),
                
                subtotal=subtotal,
                status='pending',
                payment_status='pending',
            )
            
            # Link to user if authenticated
            if request.user.is_authenticated:
                order.user = request.user
            
            # Calculate shipping fee
            shipping_fees = {
                'standard': Decimal('2500'),
                'express': Decimal('5000'),
                'pickup': Decimal('0'),
            }
            order.shipping_fee = shipping_fees.get(order.shipping_method, Decimal('2500'))
            
            # Calculate total
            order.total = order.subtotal + order.shipping_fee
            
            order.save()
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku or '',
                    variant_name=cart_item.variant.name if cart_item.variant else '',
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total=cart_item.total_price,
                )
                
                # Update product stock
                if cart_item.variant:
                    cart_item.variant.stock_quantity -= cart_item.quantity
                    cart_item.variant.save()
                else:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
            
            # Clear the cart
            clear_cart(request)
            
            # Handle payment based on method
            if order.payment_method == 'paystack':
                return redirect('orders:initiate_paystack', order_id=order.id)
            elif order.payment_method == 'bank_transfer':
                messages.success(request, 'Order placed! Please complete bank transfer to Access Bank to confirm your order.')
                return redirect('orders:order_confirmation', order_id=order.id)
            elif order.payment_method == 'ussd':
                messages.success(request, 'Order placed! Please complete USSD payment to confirm your order.')
                return redirect('orders:order_confirmation', order_id=order.id)
            else:
                messages.success(request, 'Order placed successfully!')
                return redirect('orders:order_confirmation', order_id=order.id)
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-fill form for authenticated users
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'email': request.user.email,
                'full_name': request.user.get_full_name(),
                'phone': getattr(request.user, 'phone_number', ''),
            }
        form = CheckoutForm(initial=initial_data)
    
    # Calculate shipping options
    shipping_options = [
        {'id': 'standard', 'name': 'Standard Shipping', 'price': 2500, 'time': '5-7 business days'},
        {'id': 'express', 'name': 'Express Shipping', 'price': 5000, 'time': '2-3 business days'},
        {'id': 'next_day', 'name': 'Next Day Delivery', 'price': 10000, 'time': '1 business day'},
        {'id': 'pickup', 'name': 'Store Pickup', 'price': 0, 'time': 'Ready in 24 hours'},
    ]
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'form': form,
        'shipping_options': shipping_options,
    }
    
    return render(request, 'orders/checkout.html', context)


def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Only allow user to view their own order
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('store:home')
    else:
        # For guest orders, you might want to add session-based verification
        pass
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_confirmation.html', context)


@login_required
def order_detail(request, order_id):
    """Display order detail page for authenticated users"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_detail.html', context)


# Payment gateway views
def initiate_paystack(request, order_id):
    """Initiate Paystack payment"""
    order = get_object_or_404(Order, id=order_id)
    
    # Verify user owns this order
    if request.user.is_authenticated and order.user != request.user:
        messages.error(request, 'You do not have permission to access this order.')
        return redirect('store:home')
    
    # Paystack integration
    import requests
    
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    callback_url = request.build_absolute_uri(reverse('orders:paystack_callback'))
    
    data = {
        'email': order.customer_email,
        'amount': int(order.total * 100),  # Convert to kobo (Paystack uses kobo)
        'reference': order.order_number,
        'callback_url': callback_url,
        'metadata': {
            'order_id': order.id,
            'order_number': order.order_number,
            'customer_name': order.shipping_full_name,
        }
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            if payment_data.get('status'):
                # Redirect to Paystack checkout page
                return redirect(payment_data['data']['authorization_url'])
        
        # If we get here, something went wrong
        messages.error(request, 'Payment initiation failed. Please try again.')
        return redirect('orders:order_confirmation', order_id=order.id)
        
    except requests.exceptions.RequestException as e:
        messages.error(request, 'Could not connect to payment gateway. Please try again.')
        return redirect('orders:order_confirmation', order_id=order.id)


def paystack_callback(request):
    """Handle Paystack payment callback"""
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('store:home')
    
    # Verify payment with Paystack API
    import requests
    
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    
    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            
            if payment_data.get('status') and payment_data['data']['status'] == 'success':
                # Payment successful - update order
                try:
                    order = Order.objects.get(order_number=reference)
                    order.payment_status = 'paid'
                    order.transaction_id = payment_data['data']['reference']
                    order.payment_reference = payment_data['data'].get('id', '')
                    order.status = 'confirmed'
                    order.save()
                    
                    messages.success(request, 'Payment successful! Your order has been confirmed.')
                    return redirect('orders:order_confirmation', order_id=order.id)
                    
                except Order.DoesNotExist:
                    messages.error(request, 'Order not found.')
                    return redirect('store:home')
            else:
                # Payment failed or pending
                messages.warning(request, 'Payment was not successful. Please try again.')
                try:
                    order = Order.objects.get(order_number=reference)
                    return redirect('orders:order_confirmation', order_id=order.id)
                except Order.DoesNotExist:
                    return redirect('store:home')
                    
    except requests.exceptions.RequestException:
        messages.error(request, 'Could not verify payment. Please contact support.')
    
    return redirect('store:home')


def initiate_flutterwave(request, order_id):
    """Initiate Flutterwave payment"""
    order = get_object_or_404(Order, id=order_id)
    
    # TODO: Implement actual Flutterwave integration
    # For now, redirect to confirmation
    messages.info(request, 'Flutterwave payment integration coming soon. Order placed as pending.')
    return redirect('orders:order_confirmation', order_id=order.id)


def flutterwave_callback(request):
    """Handle Flutterwave payment callback"""
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')
    
    if tx_ref and status == 'successful':
        # TODO: Verify payment with Flutterwave API
        # Update order payment status
        pass
    
    return redirect('store:home')
