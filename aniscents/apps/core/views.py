from django.shortcuts import render
from store.models import Product, Category

def home(request):
	featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
	new_arrivals = Product.objects.filter(is_new=True, is_active=True)[:8]
	bestsellers = Product.objects.filter(is_bestseller=True, is_active=True)[:8]
	categories = Category.objects.filter(is_active=True)[:6]
    
	context = {
		'featured_products': featured_products,
		'new_arrivals': new_arrivals,
		'bestsellers': bestsellers,
		'categories': categories,
	}
	return render(request, 'pages/index.html', context)
