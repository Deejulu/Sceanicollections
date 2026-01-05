"""
Cart context processor to make cart available in all templates.
"""
from .cart import get_cart_summary

def cart(request):
	"""
	Add cart data to template context.
	"""
	if request.path.startswith('/admin/'):
		return {}
	cart_data = get_cart_summary(request)
	return {
		'cart': cart_data,
		'cart_total_items': cart_data['total_items'],
		'cart_subtotal': cart_data['subtotal'],
		'cart_total': cart_data['total'],
	}
