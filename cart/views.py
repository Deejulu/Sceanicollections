from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from store.models import Product
from .models import Cart, CartItem
from .cart import get_cart

def cart_detail(request):
	cart = get_cart(request)
	context = {'cart': cart}
	return render(request, 'cart/cart_detail.html', context)


@require_POST
def cart_add(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	cart = get_cart(request)
	quantity = int(request.POST.get('quantity', 1))
	
	# Check stock availability
	if product.stock_quantity < quantity:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
				'success': False,
				'message': f"Sorry, only {product.stock_quantity} items available in stock."
			}, status=400)
		messages.error(request, f"Sorry, only {product.stock_quantity} items available in stock.")
		return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))
	
	cart_item, created = CartItem.objects.get_or_create(
		cart=cart,
		product=product,
		defaults={'quantity': quantity}
	)
	if not created:
		cart_item.quantity += quantity
		cart_item.save()
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'message': f'{product.name} added to cart!',
			'cart_total_items': cart.total_items,
			'cart_subtotal': float(cart.subtotal),
			'item_quantity': cart_item.quantity,
			'product_name': product.name,
			'product_id': product.id,
		})
	
	messages.success(request, f"{product.name} added to cart!")
	return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))


@require_POST
def cart_update(request, item_id):
	cart = get_cart(request)
	cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
	quantity = int(request.POST.get('quantity', 1))
	
	if quantity < 1:
		cart_item.delete()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
				'success': True,
				'removed': True,
				'message': f'{cart_item.product.name} removed from cart.',
				'cart_total_items': cart.total_items,
				'cart_subtotal': float(cart.subtotal),
			})
		messages.success(request, f"{cart_item.product.name} removed from cart.")
		return redirect('cart:detail')
	
	# Check stock
	if cart_item.product.stock_quantity < quantity:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
				'success': False,
				'message': f"Sorry, only {cart_item.product.stock_quantity} items available."
			}, status=400)
		messages.error(request, f"Sorry, only {cart_item.product.stock_quantity} items available.")
		return redirect('cart:detail')
	
	cart_item.quantity = quantity
	cart_item.save()
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'message': f'Cart updated.',
			'cart_total_items': cart.total_items,
			'cart_subtotal': float(cart.subtotal),
			'item_id': item_id,
			'item_quantity': cart_item.quantity,
			'item_total': float(cart_item.total_price),
		})
	
	messages.success(request, f"Updated quantity for {cart_item.product.name}.")
	return redirect('cart:detail')


@require_POST
def cart_remove(request, item_id):
	cart = get_cart(request)
	cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
	product_name = cart_item.product.name
	cart_item.delete()
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'message': f'{product_name} removed from cart.',
			'cart_total_items': cart.total_items,
			'cart_subtotal': float(cart.subtotal),
		})
	
	messages.success(request, "Item removed from cart.")
	return redirect('cart:detail')


@require_POST
def cart_clear(request):
	cart = get_cart(request)
	cart.items.all().delete()
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'message': 'Cart cleared.',
			'cart_total_items': 0,
			'cart_subtotal': 0,
		})
	
	messages.success(request, "Cart cleared.")
	return redirect('cart:detail')


@require_POST
def apply_coupon(request):
	"""Apply a coupon code to the cart."""
	cart = get_cart(request)
	code = request.POST.get('coupon_code', '').strip()
	
	if not code:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
				'success': False,
				'message': 'Please enter a coupon code.'
			}, status=400)
		messages.error(request, 'Please enter a coupon code.')
		return redirect('cart:detail')
	
	user = request.user if request.user.is_authenticated else None
	success, message = cart.apply_coupon(code, user)
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		if success:
			return JsonResponse({
				'success': True,
				'message': message,
				'cart_subtotal': float(cart.subtotal),
				'discount_amount': float(cart.discount_amount),
				'cart_total': float(cart.total),
				'coupon_code': cart.coupon.code,
				'coupon_display': cart.coupon.get_discount_display(),
			})
		return JsonResponse({
			'success': False,
			'message': message
		}, status=400)
	
	if success:
		messages.success(request, message)
	else:
		messages.error(request, message)
	return redirect('cart:detail')


@require_POST
def remove_coupon(request):
	"""Remove coupon from cart."""
	cart = get_cart(request)
	cart.remove_coupon()
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'message': 'Coupon removed.',
			'cart_subtotal': float(cart.subtotal),
			'discount_amount': 0,
			'cart_total': float(cart.total),
		})
	
	messages.success(request, "Coupon removed.")
	return redirect('cart:detail')
