"""
Cart management utility functions.
"""
from django.conf import settings
from .models import Cart, CartItem

def get_cart(request):
	"""
	Get or create cart for the current user/session.
	"""
	if request.user.is_authenticated:
		# Try to get user's active cart
		cart, created = Cart.objects.get_or_create(
			user=request.user,
			is_active=True,
			defaults={'session_key': request.session.session_key}
		)
		# If user has a session cart, merge it
		session_cart = Cart.objects.filter(
			session_key=request.session.session_key,
			is_active=True,
			user=None
		).first()
		if session_cart and session_cart != cart:
			# Merge session cart items into user cart
			for session_item in session_cart.items.all():
				cart_item, created = CartItem.objects.get_or_create(
					cart=cart,
					product=session_item.product,
					variant=session_item.variant,
					defaults={'quantity': session_item.quantity}
				)
				if not created:
					cart_item.quantity += session_item.quantity
					cart_item.save()
			# Deactivate session cart
			session_cart.is_active = False
			session_cart.save()
		return cart
	else:
		# Anonymous user - use session
		if not request.session.session_key:
			request.session.create()
		cart, created = Cart.objects.get_or_create(
			session_key=request.session.session_key,
			user=None,
			is_active=True
		)
		return cart

def add_to_cart(request, product_id, quantity=1, variant_id=None):
	"""
	Add product to cart.
	"""
	from store.models import Product, ProductVariant
	try:
		product = Product.objects.get(id=product_id, is_available=True)
		# Check variant
		variant = None
		if variant_id:
			variant = ProductVariant.objects.get(id=variant_id, product=product)
			if variant.stock_quantity < quantity:
				return False, "Insufficient stock for selected variant"
		else:
			if product.stock_quantity < quantity:
				return False, "Insufficient stock"
		cart = get_cart(request)
		cart_item, created = CartItem.objects.get_or_create(
			cart=cart,
			product=product,
			variant=variant,
			defaults={'quantity': quantity}
		)
		if not created:
			cart_item.quantity += quantity
			cart_item.save()
		return True, "Product added to cart"
	except Product.DoesNotExist:
		return False, "Product not found"
	except ProductVariant.DoesNotExist:
		return False, "Variant not found"

def update_cart_item(request, item_id, quantity):
	"""
	Update cart item quantity.
	"""
	try:
		cart = get_cart(request)
		cart_item = cart.items.get(id=item_id)
		if quantity <= 0:
			cart_item.delete()
			return True, "Item removed from cart"
		# Check stock
		product = cart_item.product
		variant = cart_item.variant
		if variant:
			if variant.stock_quantity < quantity:
				return False, f"Only {variant.stock_quantity} available in stock"
		else:
			if product.stock_quantity < quantity:
				return False, f"Only {product.stock_quantity} available in stock"
		cart_item.quantity = quantity
		cart_item.save()
		return True, "Cart updated"
	except CartItem.DoesNotExist:
		return False, "Item not found in cart"

def remove_from_cart(request, item_id):
	"""
	Remove item from cart.
	"""
	try:
		cart = get_cart(request)
		cart_item = cart.items.get(id=item_id)
		cart_item.delete()
		return True, "Item removed from cart"
	except CartItem.DoesNotExist:
		return False, "Item not found in cart"

def clear_cart(request):
	"""
	Clear all items from cart.
	"""
	cart = get_cart(request)
	cart.clear()
	return True, "Cart cleared"

def get_cart_summary(request):
	"""
	Get cart summary for templates.
	"""
	cart = get_cart(request)
	return {
		'total_items': cart.total_items,
		'subtotal': cart.subtotal,
		'shipping': cart.estimated_shipping_cost,
		'total': cart.total,
		'items': cart.items.all()
	}
