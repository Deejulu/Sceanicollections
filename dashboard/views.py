from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.core.paginator import Paginator
from datetime import timedelta
import json

from orders.models import Order
from store.models import Product, Category, ProductImage
from store.cms_models import ShopPageContent, SiteSettings, HeroSection, HomepageSection, PromotionalBanner, PageContent
from accounts.models import User, Wishlist
from feedback.models import Feedback
def customer_required(function=None):
	"""
	Decorator for views that require the user to be a customer.
	"""
	actual_decorator = user_passes_test(
		lambda u: u.is_authenticated and u.is_customer_user,
		login_url='/accounts/login/'
	)
	if function:
		return actual_decorator(function)
	return actual_decorator

def admin_required(function=None):
	"""
	Decorator for views that require admin access.
	"""
	actual_decorator = user_passes_test(
		lambda u: u.is_authenticated and u.is_admin_user,
		login_url='/accounts/login/'
	)
	if function:
		return actual_decorator(function)
	return actual_decorator


def get_admin_sidebar_context():
	"""Get common context data for admin sidebar badges."""
	today = timezone.now().date()
	return {
		'pending_orders_count': Order.objects.filter(status='pending').count(),
		'low_stock_count': Product.objects.filter(stock_quantity__lte=5, stock_quantity__gt=0).count(),
		'new_feedback_count': Feedback.objects.filter(status='new').count(),
		'today_orders': Order.objects.filter(created_at__date=today).count(),
		'today_revenue': Order.objects.filter(created_at__date=today, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0,
		'new_customers': User.objects.filter(date_joined__date=today, user_type='customer').count(),
	}


from django.contrib.auth.decorators import login_required

@login_required
def customer_dashboard(request):
	"""
	Comprehensive Customer dashboard view with all relevant data.
	"""
	user = request.user
	orders = Order.objects.filter(user=user)
	
	# Order statistics
	total_orders = orders.count()
	delivered_orders_count = orders.filter(status='delivered').count()
	pending_processing_orders_count = orders.filter(status__in=['pending', 'processing', 'confirmed']).count()
	shipped_orders_count = orders.filter(status='shipped').count()
	cancelled_orders_count = orders.filter(status='cancelled').count()
	
	# Financial statistics
	total_spent = orders.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
	
	# Recent orders (last 5)
	recent_orders = orders.order_by('-created_at')[:5]
	
	# Orders in transit (shipped but not delivered)
	orders_in_transit = orders.filter(status='shipped').order_by('-created_at')[:3]
	
	# Pending orders requiring attention
	pending_orders = orders.filter(status__in=['pending', 'confirmed']).order_by('-created_at')[:3]
	
	# Wishlist items
	wishlist_items = []
	if hasattr(user, 'wishlist') and user.wishlist:
		wishlist_items = user.wishlist.products.all()[:4]
	
	# Account completion percentage
	profile_fields = [user.first_name, user.last_name, user.phone, user.email]
	completed_fields = sum(1 for f in profile_fields if f)
	profile_completion = int((completed_fields / len(profile_fields)) * 100)
	
	# Address count
	address_count = user.addresses.count() if hasattr(user, 'addresses') else 0
	
	context = {
		'user': user,
		'total_orders': total_orders,
		'delivered_orders_count': delivered_orders_count,
		'pending_processing_orders_count': pending_processing_orders_count,
		'shipped_orders_count': shipped_orders_count,
		'cancelled_orders_count': cancelled_orders_count,
		'total_spent': total_spent,
		'recent_orders': recent_orders,
		'orders_in_transit': orders_in_transit,
		'pending_orders': pending_orders,
		'wishlist_items': wishlist_items,
		'profile_completion': profile_completion,
		'address_count': address_count,
		'title': 'My Dashboard',
		'dashboard_active': 'overview',
	}
	return render(request, 'dashboard/customer/dashboard.html', context)

@customer_required
def customer_orders(request):
	orders = Order.objects.filter(user=request.user).order_by('-created_at')
	pending_orders_count = orders.filter(status='pending').count()
	context = {
		'orders': orders,
		'pending_orders_count': pending_orders_count,
		'title': 'My Orders',
		'dashboard_active': 'orders',
	}
	return render(request, 'dashboard/customer/orders.html', context)

@customer_required
def customer_wishlist(request):
	# Get or create wishlist for user
	wishlist, created = Wishlist.objects.get_or_create(user=request.user)
	wishlist_products = wishlist.products.all() if wishlist else []
	
	context = {
		'wishlist': wishlist,
		'wishlist_products': wishlist_products,
		'title': 'My Wishlist',
		'dashboard_active': 'wishlist',
	}
	return render(request, 'dashboard/customer/wishlist.html', context)

@customer_required
def wishlist_add(request, product_id):
	"""Add product to wishlist."""
	product = get_object_or_404(Product, id=product_id)
	wishlist, created = Wishlist.objects.get_or_create(user=request.user)
	wishlist.add_product(product)
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({'status': 'success', 'message': 'Added to wishlist', 'count': wishlist.count})
	
	messages.success(request, f'{product.name} added to your wishlist!')
	return redirect(request.META.get('HTTP_REFERER', 'dashboard:customer_wishlist'))

@customer_required  
def wishlist_remove(request, product_id):
	"""Remove product from wishlist."""
	product = get_object_or_404(Product, id=product_id)
	wishlist = getattr(request.user, 'wishlist', None)
	
	if wishlist:
		wishlist.remove_product(product)
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({'status': 'success', 'message': 'Removed from wishlist', 'count': wishlist.count if wishlist else 0})
	
	messages.success(request, f'{product.name} removed from your wishlist.')
	return redirect('dashboard:customer_wishlist')

@customer_required
def wishlist_toggle(request, product_id):
	"""Toggle product in wishlist (add if not present, remove if present)."""
	product = get_object_or_404(Product, id=product_id)
	wishlist, created = Wishlist.objects.get_or_create(user=request.user)
	
	if wishlist.contains(product):
		wishlist.remove_product(product)
		action = 'removed'
		message = f'{product.name} removed from wishlist'
	else:
		wishlist.add_product(product)
		action = 'added'
		message = f'{product.name} added to wishlist'
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'status': 'success', 
			'action': action,
			'message': message, 
			'count': wishlist.count,
			'in_wishlist': wishlist.contains(product)
		})
	
	messages.success(request, message)
	return redirect(request.META.get('HTTP_REFERER', 'dashboard:customer_wishlist'))

@customer_required
def customer_profile(request):
	user = request.user
	if request.method == 'POST':
		user.first_name = request.POST.get('first_name', user.first_name)
		user.last_name = request.POST.get('last_name', user.last_name)
		user.phone = request.POST.get('phone', user.phone)
		user.save()
	context = {
		'user': user,
		'title': 'My Profile',
		'dashboard_active': 'profile',
	}
	return render(request, 'dashboard/customer/profile.html', context)

@customer_required
def customer_addresses(request):
	addresses = request.user.addresses.all() if hasattr(request.user, 'addresses') else []
	context = {
		'addresses': addresses,
		'title': 'My Addresses',
		'dashboard_active': 'addresses',
	}
	return render(request, 'dashboard/customer/addresses.html', context)

@admin_required
def admin_dashboard(request):
	today = timezone.now().date()
	total_orders = Order.objects.count()
	recent_orders = Order.objects.filter(created_at__date=today).count()
	pending_orders = Order.objects.filter(status='pending').count()
	total_sales = Order.objects.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
	today_sales = Order.objects.filter(created_at__date=today, payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
	total_products = Product.objects.count()
	low_stock_products = Product.objects.filter(stock_quantity__lte=5, stock_quantity__gt=0).count()
	out_of_stock_products = Product.objects.filter(stock_quantity=0).count()
	total_customers = User.objects.filter(user_type='customer').count()
	new_customers_today = User.objects.filter(date_joined__date=today, user_type='customer').count()
	recent_orders_list = Order.objects.order_by('-created_at')[:10]
	best_sellers = Product.objects.order_by('-purchase_count')[:5]
	context = {
		'total_orders': total_orders,
		'recent_orders': recent_orders,
		'pending_orders': pending_orders,
		'total_sales': total_sales,
		'today_sales': today_sales,
		'total_products': total_products,
		'low_stock_products': low_stock_products,
		'out_of_stock_products': out_of_stock_products,
		'total_customers': total_customers,
		'new_customers_today': new_customers_today,
		'recent_orders_list': recent_orders_list,
		'best_sellers': best_sellers,
		'title': 'Admin Dashboard',
		'admin_active': 'overview',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/dashboard.html', context)

@admin_required
def admin_orders(request):
	orders = Order.objects.all().order_by('-created_at')
	status_filter = request.GET.get('status')
	payment_filter = request.GET.get('payment')
	search_query = request.GET.get('q')
	
	if status_filter:
		orders = orders.filter(status=status_filter)
	if payment_filter:
		orders = orders.filter(payment_status=payment_filter)
	if search_query:
		orders = orders.filter(
			Q(order_number__icontains=search_query) |
			Q(customer_name__icontains=search_query) |
			Q(customer_email__icontains=search_query)
		)
	
	# Stats
	total_orders = Order.objects.count()
	pending_count = Order.objects.filter(status='pending').count()
	processing_count = Order.objects.filter(status__in=['confirmed', 'processing']).count()
	shipped_count = Order.objects.filter(status='shipped').count()
	delivered_count = Order.objects.filter(status='delivered').count()
	awaiting_payment_count = Order.objects.filter(payment_status='pending').count()
	
	# Pagination
	paginator = Paginator(orders, 20)
	page = request.GET.get('page', 1)
	orders = paginator.get_page(page)
	
	context = {
		'orders': orders,
		'total_orders': total_orders,
		'pending_count': pending_count,
		'processing_count': processing_count,
		'shipped_count': shipped_count,
		'delivered_count': delivered_count,
		'awaiting_payment_count': awaiting_payment_count,
		'current_status': status_filter,
		'current_payment': payment_filter,
		'search_query': search_query,
		'title': 'Manage Orders',
		'admin_active': 'orders',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/orders.html', context)

@admin_required
def admin_products(request):
	products = Product.objects.all().order_by('-created_at')
	category_filter = request.GET.get('category')
	if category_filter:
		products = products.filter(category_id=category_filter)
	stock_filter = request.GET.get('stock')
	if stock_filter == 'low':
		products = products.filter(stock_quantity__lte=5, stock_quantity__gt=0)
	elif stock_filter == 'out':
		products = products.filter(stock_quantity=0)
	elif stock_filter == 'in':
		products = products.filter(stock_quantity__gt=5)
	
	# Stats
	total_products = Product.objects.count()
	in_stock_count = Product.objects.filter(stock_quantity__gt=5).count()
	low_stock_count = Product.objects.filter(stock_quantity__lte=5, stock_quantity__gt=0).count()
	out_of_stock_count = Product.objects.filter(stock_quantity=0).count()
	
	# Categories for filter
	categories = Category.objects.all()
	
	# Pagination
	paginator = Paginator(products, 12)
	page = request.GET.get('page', 1)
	products = paginator.get_page(page)
	
	context = {
		'products': products,
		'categories': categories,
		'total_products': total_products,
		'in_stock_count': in_stock_count,
		'low_stock_count': low_stock_count,
		'out_of_stock_count': out_of_stock_count,
		'stock_filter': stock_filter,
		'category_filter': category_filter,
		'title': 'Manage Products',
		'admin_active': 'products',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/products.html', context)

@admin_required
def admin_customers(request):
	customers = User.objects.filter(user_type='customer').order_by('-date_joined')
	
	# Sorting
	sort = request.GET.get('sort', 'newest')
	if sort == 'oldest':
		customers = customers.order_by('date_joined')
	elif sort == 'name':
		customers = customers.order_by('first_name', 'last_name')
	elif sort == 'orders':
		customers = customers.annotate(order_count=Count('orders')).order_by('-order_count')
	elif sort == 'spent':
		customers = customers.annotate(total_spent=Sum('orders__total')).order_by('-total_spent')
	
	# Add total_spent annotation
	customers = customers.annotate(
		total_spent=Sum('orders__total', filter=Q(orders__payment_status='paid')),
		order_count=Count('orders')
	)
	
	# Search
	search_query = request.GET.get('q')
	if search_query:
		customers = customers.filter(
			Q(first_name__icontains=search_query) |
			Q(last_name__icontains=search_query) |
			Q(email__icontains=search_query)
		)
	
	# Stats
	today = timezone.now().date()
	total_customers = User.objects.filter(user_type='customer').count()
	active_today = User.objects.filter(user_type='customer', last_login__date=today).count()
	new_this_month = User.objects.filter(
		user_type='customer', 
		date_joined__month=today.month,
		date_joined__year=today.year
	).count()
	customers_with_orders = User.objects.filter(user_type='customer', orders__isnull=False).distinct().count()
	
	# Pagination
	paginator = Paginator(customers, 20)
	page = request.GET.get('page', 1)
	customers = paginator.get_page(page)
	
	context = {
		'customers': customers,
		'total_customers': total_customers,
		'active_today': active_today,
		'new_this_month': new_this_month,
		'customers_with_orders': customers_with_orders,
		'sort': sort,
		'search_query': search_query,
		'title': 'Manage Customers',
		'admin_active': 'customers',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/customers.html', context)

@admin_required
def admin_analytics(request):
	today = timezone.now().date()
	days = int(request.GET.get('days', 30))
	start_date = today - timedelta(days=days)
	
	# Calculate metrics
	orders = Order.objects.filter(created_at__date__gte=start_date)
	paid_orders = orders.filter(payment_status='paid')
	
	total_revenue = paid_orders.aggregate(total=Sum('total'))['total'] or 0
	total_orders = orders.count()
	avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
	new_customers = User.objects.filter(user_type='customer', date_joined__date__gte=start_date).count()
	
	# Previous period for comparison
	prev_start = start_date - timedelta(days=days)
	prev_orders = Order.objects.filter(created_at__date__gte=prev_start, created_at__date__lt=start_date)
	prev_revenue = prev_orders.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
	prev_order_count = prev_orders.count()
	prev_customers = User.objects.filter(user_type='customer', date_joined__date__gte=prev_start, date_joined__date__lt=start_date).count()
	
	# Growth calculations
	revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
	orders_growth = ((total_orders - prev_order_count) / prev_order_count * 100) if prev_order_count > 0 else 0
	customers_growth = ((new_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else 0
	
	# Sales data for chart
	dates = []
	sales_data = []
	for i in range(min(7, days)):
		date = today - timedelta(days=i)
		daily_sales = Order.objects.filter(
			created_at__date=date,
			payment_status='paid'
		).aggregate(total=Sum('total'))['total'] or 0
		dates.append(date.strftime('%a'))
		sales_data.append(float(daily_sales))
	dates.reverse()
	sales_data.reverse()
	
	# Top products
	top_products = Product.objects.order_by('-purchase_count')[:5]
	
	# Category data
	category_stats = Product.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:6]
	category_labels = [cat['category__name'] or 'Uncategorized' for cat in category_stats]
	category_data = [cat['count'] for cat in category_stats]
	
	# Order status distribution
	total_all_orders = Order.objects.count()
	order_statuses = []
	for status in ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']:
		count = Order.objects.filter(status=status).count()
		percentage = (count / total_all_orders * 100) if total_all_orders > 0 else 0
		order_statuses.append({'status': status, 'count': count, 'percentage': round(percentage, 1)})
	
	# Performance metrics
	total_customer_count = User.objects.filter(user_type='customer').count()
	conversion_rate = (total_orders / total_customer_count * 100) if total_customer_count > 0 else 0
	repeat_customers = User.objects.filter(user_type='customer').annotate(order_count=Count('orders')).filter(order_count__gt=1).count()
	repeat_customer_rate = (repeat_customers / total_customer_count * 100) if total_customer_count > 0 else 0
	avg_items = Order.objects.aggregate(avg=Avg('items__quantity'))['avg'] or 0
	customer_satisfaction = Feedback.objects.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg'] or 0
	
	context = {
		'total_revenue': total_revenue,
		'total_orders': total_orders,
		'avg_order_value': avg_order_value,
		'new_customers': new_customers,
		'revenue_growth': revenue_growth,
		'orders_growth': orders_growth,
		'customers_growth': customers_growth,
		'dates': json.dumps(dates),
		'sales_data': json.dumps(sales_data),
		'top_products': top_products,
		'category_labels': json.dumps(category_labels),
		'category_data': json.dumps(category_data),
		'order_statuses': order_statuses,
		'conversion_rate': conversion_rate,
		'repeat_customer_rate': repeat_customer_rate,
		'avg_items_per_order': avg_items,
		'customer_satisfaction': customer_satisfaction,
		'days': days,
		'title': 'Analytics',
		'admin_active': 'analytics',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/analytics.html', context)


# ============================================
# ADDITIONAL ADMIN VIEWS
# ============================================

@admin_required
def admin_order_detail(request, order_id):
	order = get_object_or_404(Order, id=order_id)
	
	# Calculate status index for progress bar
	status_order = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
	status_index = status_order.index(order.status) + 1 if order.status in status_order else 1
	
	context = {
		'order': order,
		'status_index': status_index,
		'title': f'Order #{order.order_number}',
		'admin_active': 'orders',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/order_detail.html', context)


@admin_required
def admin_update_order_status(request, order_id):
	if request.method == 'POST':
		order = get_object_or_404(Order, id=order_id)
		new_status = request.POST.get('status')
		tracking_number = request.POST.get('tracking_number')
		
		if new_status:
			order.status = new_status
			if tracking_number:
				order.tracking_number = tracking_number
			order.save()
			messages.success(request, f'Order status updated to {order.get_status_display()}')
	
	return redirect('dashboard:admin_order_detail', order_id=order_id)


@admin_required
def admin_update_payment_status(request, order_id):
	if request.method == 'POST':
		order = get_object_or_404(Order, id=order_id)
		new_status = request.POST.get('payment_status')
		
		if new_status:
			order.payment_status = new_status
			order.save()
			messages.success(request, f'Payment status updated to {order.get_payment_status_display()}')
	
	return redirect('dashboard:admin_order_detail', order_id=order_id)


@admin_required
def admin_update_order_notes(request, order_id):
	if request.method == 'POST':
		order = get_object_or_404(Order, id=order_id)
		order.internal_notes = request.POST.get('internal_notes', '')
		order.save()
		messages.success(request, 'Notes saved successfully')
	
	return redirect('dashboard:admin_order_detail', order_id=order_id)


@admin_required
def admin_update_stock(request, product_id):
	if request.method == 'POST':
		product = get_object_or_404(Product, id=product_id)
		new_stock = request.POST.get('stock')
		
		if new_stock is not None:
			product.stock_quantity = int(new_stock)
			product.save()
			messages.success(request, f'Stock updated for {product.name}')
	
	return redirect('dashboard:admin_products')


@admin_required
def admin_customer_detail(request, customer_id):
	customer = get_object_or_404(User, id=customer_id, user_type='customer')
	orders = Order.objects.filter(user=customer).order_by('-created_at')
	feedbacks = Feedback.objects.filter(user=customer).order_by('-created_at')
	
	# Stats
	total_orders = orders.count()
	total_spent = orders.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
	avg_order = total_spent / total_orders if total_orders > 0 else 0
	wishlist_count = customer.wishlist.products.count() if hasattr(customer, 'wishlist') and customer.wishlist else 0
	
	context = {
		'customer': customer,
		'orders': orders,
		'feedbacks': feedbacks,
		'total_orders': total_orders,
		'total_spent': total_spent,
		'avg_order': avg_order,
		'wishlist_count': wishlist_count,
		'title': f'Customer: {customer.get_full_name()}',
		'admin_active': 'customers',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/customer_detail.html', context)


@admin_required
def admin_toggle_customer_status(request, customer_id):
	if request.method == 'POST':
		customer = get_object_or_404(User, id=customer_id, user_type='customer')
		customer.is_active = not customer.is_active
		customer.save()
		
		status = 'activated' if customer.is_active else 'deactivated'
		messages.success(request, f'Customer account {status}')
	
	return redirect('dashboard:admin_customer_detail', customer_id=customer_id)


@admin_required
def admin_feedback(request):
	feedbacks = Feedback.objects.all().order_by('-created_at')
	
	# Filter
	status_filter = request.GET.get('status')
	if status_filter:
		feedbacks = feedbacks.filter(status=status_filter)
	
	# Stats
	total_feedback = Feedback.objects.count()
	new_count = Feedback.objects.filter(status='new').count()
	pending_response = Feedback.objects.filter(status__in=['new', 'read']).count()
	avg_rating = Feedback.objects.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
	
	# Pagination
	paginator = Paginator(feedbacks, 10)
	page = request.GET.get('page', 1)
	feedbacks = paginator.get_page(page)
	
	context = {
		'feedbacks': feedbacks,
		'total_feedback': total_feedback,
		'new_count': new_count,
		'pending_response': pending_response,
		'avg_rating': avg_rating,
		'status_filter': status_filter,
		'title': 'Manage Feedback',
		'admin_active': 'feedback',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/feedback.html', context)


@admin_required
def admin_feedback_status(request, feedback_id):
	if request.method == 'POST':
		feedback = get_object_or_404(Feedback, id=feedback_id)
		new_status = request.POST.get('status')
		
		if new_status:
			feedback.status = new_status
			feedback.save()
			messages.success(request, f'Feedback marked as {feedback.get_status_display()}')
	
	return redirect('dashboard:admin_feedback')


@admin_required
def admin_feedback_respond(request, feedback_id):
	if request.method == 'POST':
		feedback = get_object_or_404(Feedback, id=feedback_id)
		
		feedback.admin_response = request.POST.get('admin_response', '')
		feedback.status = request.POST.get('status', 'responded')
		feedback.responded_by = request.user
		feedback.responded_at = timezone.now()
		feedback.save()
		
		messages.success(request, 'Response sent successfully')
	
	return redirect('dashboard:admin_feedback')


@admin_required
def admin_settings(request):
	import django
	import sys
	
	context = {
		'django_version': django.get_version(),
		'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
		'title': 'Settings',
		'admin_active': 'settings',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/settings.html', context)


@admin_required
def admin_update_profile(request):
	if request.method == 'POST':
		user = request.user
		user.first_name = request.POST.get('first_name', user.first_name)
		user.last_name = request.POST.get('last_name', user.last_name)
		user.email = request.POST.get('email', user.email)
		user.phone = request.POST.get('phone', user.phone)
		user.save()
		messages.success(request, 'Profile updated successfully!')
	
	return redirect('dashboard:admin_settings')


@admin_required
def admin_change_password(request):
	if request.method == 'POST':
		user = request.user
		current_password = request.POST.get('current_password')
		new_password = request.POST.get('new_password')
		confirm_password = request.POST.get('confirm_password')
		
		if not user.check_password(current_password):
			messages.error(request, 'Current password is incorrect')
		elif new_password != confirm_password:
			messages.error(request, 'New passwords do not match')
		elif len(new_password) < 8:
			messages.error(request, 'Password must be at least 8 characters')
		else:
			user.set_password(new_password)
			user.save()
			messages.success(request, 'Password changed successfully! Please login again.')
			return redirect('accounts:login')
	
	return redirect('dashboard:admin_settings')


# ============================================
# CMS / CONTENT MANAGEMENT VIEWS
# ============================================

@admin_required
def admin_shop_content(request):
	"""Manage shop page content."""
	shop_content = ShopPageContent.get_content()
	
	if request.method == 'POST':
		# Update shop page content
		shop_content.page_title = request.POST.get('page_title', shop_content.page_title)
		shop_content.page_subtitle = request.POST.get('page_subtitle', shop_content.page_subtitle)
		shop_content.empty_title = request.POST.get('empty_title', shop_content.empty_title)
		shop_content.empty_message = request.POST.get('empty_message', shop_content.empty_message)
		shop_content.category_filter_label = request.POST.get('category_filter_label', shop_content.category_filter_label)
		shop_content.price_filter_label = request.POST.get('price_filter_label', shop_content.price_filter_label)
		shop_content.sort_label = request.POST.get('sort_label', shop_content.sort_label)
		
		# Handle header image upload
		if 'header_image' in request.FILES:
			shop_content.header_image = request.FILES['header_image']
		
		shop_content.save()
		messages.success(request, 'Shop page content updated successfully!')
		return redirect('dashboard:admin_shop_content')
	
	context = {
		'shop_content': shop_content,
		'title': 'Shop Page Content',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/shop_content.html', context)


@admin_required
def admin_site_content(request):
	"""Overview of all site content management options."""
	site_settings = SiteSettings.get_settings()
	hero_section = HeroSection.get_active()
	shop_content = ShopPageContent.get_content()
	homepage_sections = HomepageSection.objects.filter(is_active=True).count()
	banners = PromotionalBanner.objects.filter(is_active=True).count()
	categories_count = Category.objects.count()
	products_count = Product.objects.count()
	pages_count = PageContent.objects.count()
	
	context = {
		'site_settings': site_settings,
		'hero_section': hero_section,
		'shop_content': shop_content,
		'homepage_sections_count': homepage_sections,
		'active_banners_count': banners,
		'categories_count': categories_count,
		'products_count': products_count,
		'pages_count': pages_count,
		'title': 'Content Management',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/content.html', context)


# ============================================
# CATEGORY MANAGEMENT VIEWS
# ============================================

@admin_required
def admin_categories(request):
	"""List all categories."""
	categories = Category.objects.all().order_by('name')
	
	context = {
		'categories': categories,
		'title': 'Manage Categories',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/categories.html', context)


@admin_required
def admin_category_add(request):
	"""Add a new category."""
	if request.method == 'POST':
		name = request.POST.get('name')
		description = request.POST.get('description', '')
		parent_id = request.POST.get('parent')
		is_active = request.POST.get('is_active') == 'on'
		featured = request.POST.get('featured') == 'on'
		
		category = Category(
			name=name,
			description=description,
			is_active=is_active,
			featured=featured,
		)
		
		if parent_id:
			category.parent = Category.objects.get(id=parent_id)
		
		if 'image' in request.FILES:
			category.image = request.FILES['image']
		
		category.save()
		messages.success(request, f'Category "{name}" created successfully!')
		return redirect('dashboard:admin_categories')
	
	parent_categories = Category.objects.filter(parent__isnull=True)
	
	context = {
		'parent_categories': parent_categories,
		'title': 'Add Category',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/category_form.html', context)


@admin_required
def admin_category_edit(request, category_id):
	"""Edit a category."""
	category = get_object_or_404(Category, id=category_id)
	
	if request.method == 'POST':
		category.name = request.POST.get('name', category.name)
		category.description = request.POST.get('description', '')
		parent_id = request.POST.get('parent')
		category.is_active = request.POST.get('is_active') == 'on'
		category.featured = request.POST.get('featured') == 'on'
		
		if parent_id:
			category.parent = Category.objects.get(id=parent_id)
		else:
			category.parent = None
		
		if 'image' in request.FILES:
			category.image = request.FILES['image']
		
		category.save()
		messages.success(request, f'Category "{category.name}" updated successfully!')
		return redirect('dashboard:admin_categories')
	
	parent_categories = Category.objects.filter(parent__isnull=True).exclude(id=category_id)
	
	context = {
		'category': category,
		'parent_categories': parent_categories,
		'title': f'Edit Category: {category.name}',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/category_form.html', context)


@admin_required
def admin_category_delete(request, category_id):
	"""Delete a category."""
	category = get_object_or_404(Category, id=category_id)
	
	if request.method == 'POST':
		name = category.name
		category.delete()
		messages.success(request, f'Category "{name}" deleted successfully!')
	
	return redirect('dashboard:admin_categories')


# ============================================
# PRODUCT MANAGEMENT VIEWS (Add/Edit)
# ============================================

@admin_required
def admin_product_add(request):
	"""Add a new product."""
	if request.method == 'POST':
		product = Product(
			name=request.POST.get('name'),
			category_id=request.POST.get('category'),
			concentration=request.POST.get('concentration', 'edp'),
			gender=request.POST.get('gender', 'unisex'),
			size_ml=request.POST.get('size_ml', 100),
			short_description=request.POST.get('short_description', ''),
			full_description=request.POST.get('full_description', ''),
			price=request.POST.get('price'),
			compare_price=request.POST.get('compare_price') or None,
			stock_quantity=request.POST.get('stock_quantity', 0),
			top_notes=request.POST.get('top_notes', ''),
			heart_notes=request.POST.get('heart_notes', ''),
			base_notes=request.POST.get('base_notes', ''),
			longevity=request.POST.get('longevity', ''),
			sillage=request.POST.get('sillage', ''),
			is_featured=request.POST.get('is_featured') == 'on',
			is_bestseller=request.POST.get('is_bestseller') == 'on',
			is_new=request.POST.get('is_new') == 'on',
			is_available=request.POST.get('is_available') == 'on',
		)
		product.save()
		
		# Handle product images
		if 'images' in request.FILES:
			for i, image in enumerate(request.FILES.getlist('images')):
				ProductImage.objects.create(
					product=product,
					image=image,
					is_primary=(i == 0)
				)
		
		messages.success(request, f'Product "{product.name}" created successfully!')
		return redirect('dashboard:admin_products')
	
	categories = Category.objects.filter(is_active=True)
	
	context = {
		'categories': categories,
		'concentration_choices': Product.CONCENTRATION_CHOICES,
		'gender_choices': Product.GENDER_CHOICES,
		'title': 'Add Product',
		'admin_active': 'products',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/product_form.html', context)


@admin_required
def admin_product_edit(request, product_id):
	"""Edit a product."""
	product = get_object_or_404(Product, id=product_id)
	
	if request.method == 'POST':
		product.name = request.POST.get('name', product.name)
		product.category_id = request.POST.get('category', product.category_id)
		product.concentration = request.POST.get('concentration', product.concentration)
		product.gender = request.POST.get('gender', product.gender)
		product.size_ml = request.POST.get('size_ml', product.size_ml)
		product.short_description = request.POST.get('short_description', '')
		product.full_description = request.POST.get('full_description', '')
		product.price = request.POST.get('price', product.price)
		product.compare_price = request.POST.get('compare_price') or None
		product.stock_quantity = request.POST.get('stock_quantity', product.stock_quantity)
		product.top_notes = request.POST.get('top_notes', '')
		product.heart_notes = request.POST.get('heart_notes', '')
		product.base_notes = request.POST.get('base_notes', '')
		product.longevity = request.POST.get('longevity', '')
		product.sillage = request.POST.get('sillage', '')
		product.is_featured = request.POST.get('is_featured') == 'on'
		product.is_bestseller = request.POST.get('is_bestseller') == 'on'
		product.is_new = request.POST.get('is_new') == 'on'
		product.is_available = request.POST.get('is_available') == 'on'
		product.save()
		
		# Handle new product images
		if 'images' in request.FILES:
			for image in request.FILES.getlist('images'):
				ProductImage.objects.create(
					product=product,
					image=image,
					is_primary=False
				)
		
		messages.success(request, f'Product "{product.name}" updated successfully!')
		return redirect('dashboard:admin_products')
	
	categories = Category.objects.filter(is_active=True)
	
	context = {
		'product': product,
		'categories': categories,
		'concentration_choices': Product.CONCENTRATION_CHOICES,
		'gender_choices': Product.GENDER_CHOICES,
		'title': f'Edit Product: {product.name}',
		'admin_active': 'products',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/product_form.html', context)


@admin_required
def admin_product_delete(request, product_id):
	"""Delete a product."""
	product = get_object_or_404(Product, id=product_id)
	
	if request.method == 'POST':
		name = product.name
		product.delete()
		messages.success(request, f'Product "{name}" deleted successfully!')
	
	return redirect('dashboard:admin_products')


@admin_required
def admin_product_image_delete(request, image_id):
	"""Delete a product image."""
	image = get_object_or_404(ProductImage, id=image_id)
	product_id = image.product.id
	image.delete()
	messages.success(request, 'Image deleted successfully!')
	return redirect('dashboard:admin_product_edit', product_id=product_id)


# ============================================
# HERO SECTION MANAGEMENT
# ============================================

@admin_required
def admin_hero_section(request):
	"""Edit hero section content."""
	hero = HeroSection.get_active()
	if not hero:
		hero = HeroSection.objects.create()
	
	if request.method == 'POST':
		hero.badge_text = request.POST.get('badge_text', '')
		hero.title_line1 = request.POST.get('title_line1', '')
		hero.title_line2 = request.POST.get('title_line2', '')
		hero.subtitle = request.POST.get('subtitle', '')
		hero.cta_primary_text = request.POST.get('cta_primary_text', '')
		hero.cta_primary_url = request.POST.get('cta_primary_url', '')
		hero.cta_secondary_text = request.POST.get('cta_secondary_text', '')
		hero.cta_secondary_url = request.POST.get('cta_secondary_url', '')
		hero.stat1_value = request.POST.get('stat1_value', '')
		hero.stat1_label = request.POST.get('stat1_label', '')
		hero.stat2_value = request.POST.get('stat2_value', '')
		hero.stat2_label = request.POST.get('stat2_label', '')
		hero.stat3_value = request.POST.get('stat3_value', '')
		hero.stat3_label = request.POST.get('stat3_label', '')
		hero.card1_title = request.POST.get('card1_title', '')
		hero.card1_subtitle = request.POST.get('card1_subtitle', '')
		hero.card1_icon = request.POST.get('card1_icon', '')
		hero.card2_title = request.POST.get('card2_title', '')
		hero.card2_subtitle = request.POST.get('card2_subtitle', '')
		hero.card2_icon = request.POST.get('card2_icon', '')
		hero.hero_image_url = request.POST.get('hero_image_url', '')
		hero.is_active = request.POST.get('is_active') == 'on'
		
		if 'hero_image' in request.FILES:
			hero.hero_image = request.FILES['hero_image']
		
		hero.save()
		messages.success(request, 'Hero section updated successfully!')
		return redirect('dashboard:admin_hero_section')
	
	context = {
		'hero': hero,
		'title': 'Hero Section',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/hero_section.html', context)


# ============================================
# HOMEPAGE SECTIONS MANAGEMENT
# ============================================

@admin_required
def admin_homepage_sections(request):
	"""List all homepage sections."""
	sections = HomepageSection.objects.all().order_by('display_order')
	
	context = {
		'sections': sections,
		'title': 'Homepage Sections',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/homepage_sections.html', context)


@admin_required
def admin_homepage_section_add(request):
	"""Add a new homepage section."""
	if request.method == 'POST':
		section = HomepageSection(
			section_type=request.POST.get('section_type'),
			title=request.POST.get('title'),
			subtitle=request.POST.get('subtitle', ''),
			badge_text=request.POST.get('badge_text', ''),
			banner_url=request.POST.get('banner_url', ''),
			banner_button_text=request.POST.get('banner_button_text', ''),
			custom_content=request.POST.get('custom_content', ''),
			display_order=request.POST.get('display_order', 0),
			products_to_show=request.POST.get('products_to_show', 4),
			is_active=request.POST.get('is_active') == 'on',
		)
		
		if 'banner_image' in request.FILES:
			section.banner_image = request.FILES['banner_image']
		
		section.save()
		messages.success(request, f'Section "{section.title}" created successfully!')
		return redirect('dashboard:admin_homepage_sections')
	
	context = {
		'section_types': HomepageSection.SECTION_TYPES,
		'title': 'Add Homepage Section',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/homepage_section_form.html', context)


@admin_required
def admin_homepage_section_edit(request, section_id):
	"""Edit a homepage section."""
	section = get_object_or_404(HomepageSection, id=section_id)
	
	if request.method == 'POST':
		section.section_type = request.POST.get('section_type', section.section_type)
		section.title = request.POST.get('title', section.title)
		section.subtitle = request.POST.get('subtitle', '')
		section.badge_text = request.POST.get('badge_text', '')
		section.banner_url = request.POST.get('banner_url', '')
		section.banner_button_text = request.POST.get('banner_button_text', '')
		section.custom_content = request.POST.get('custom_content', '')
		section.display_order = request.POST.get('display_order', section.display_order)
		section.products_to_show = request.POST.get('products_to_show', section.products_to_show)
		section.is_active = request.POST.get('is_active') == 'on'
		
		if 'banner_image' in request.FILES:
			section.banner_image = request.FILES['banner_image']
		
		section.save()
		messages.success(request, f'Section "{section.title}" updated successfully!')
		return redirect('dashboard:admin_homepage_sections')
	
	context = {
		'section': section,
		'section_types': HomepageSection.SECTION_TYPES,
		'title': f'Edit Section: {section.title}',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/homepage_section_form.html', context)


@admin_required
def admin_homepage_section_delete(request, section_id):
	"""Delete a homepage section."""
	section = get_object_or_404(HomepageSection, id=section_id)
	
	if request.method == 'POST':
		title = section.title
		section.delete()
		messages.success(request, f'Section "{title}" deleted successfully!')
	
	return redirect('dashboard:admin_homepage_sections')


# ============================================
# PROMOTIONAL BANNERS MANAGEMENT
# ============================================

@admin_required
def admin_banners(request):
	"""List all promotional banners."""
	banners = PromotionalBanner.objects.all().order_by('-created_at')
	
	context = {
		'banners': banners,
		'title': 'Promotional Banners',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/banners.html', context)


@admin_required
def admin_banner_add(request):
	"""Add a new promotional banner."""
	if request.method == 'POST':
		banner = PromotionalBanner(
			name=request.POST.get('name'),
			position=request.POST.get('position'),
			text=request.POST.get('text', ''),
			subtext=request.POST.get('subtext', ''),
			background_color=request.POST.get('background_color', '#D4AF37'),
			text_color=request.POST.get('text_color', '#1a1a2e'),
			link_url=request.POST.get('link_url', ''),
			link_text=request.POST.get('link_text', ''),
			is_active=request.POST.get('is_active') == 'on',
		)
		
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		if start_date:
			banner.start_date = start_date
		if end_date:
			banner.end_date = end_date
		
		if 'image' in request.FILES:
			banner.image = request.FILES['image']
		
		banner.save()
		messages.success(request, f'Banner "{banner.name}" created successfully!')
		return redirect('dashboard:admin_banners')
	
	context = {
		'position_choices': PromotionalBanner.POSITION_CHOICES,
		'title': 'Add Banner',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/banner_form.html', context)


@admin_required
def admin_banner_edit(request, banner_id):
	"""Edit a promotional banner."""
	banner = get_object_or_404(PromotionalBanner, id=banner_id)
	
	if request.method == 'POST':
		banner.name = request.POST.get('name', banner.name)
		banner.position = request.POST.get('position', banner.position)
		banner.text = request.POST.get('text', '')
		banner.subtext = request.POST.get('subtext', '')
		banner.background_color = request.POST.get('background_color', '#D4AF37')
		banner.text_color = request.POST.get('text_color', '#1a1a2e')
		banner.link_url = request.POST.get('link_url', '')
		banner.link_text = request.POST.get('link_text', '')
		banner.is_active = request.POST.get('is_active') == 'on'
		
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		banner.start_date = start_date if start_date else None
		banner.end_date = end_date if end_date else None
		
		if 'image' in request.FILES:
			banner.image = request.FILES['image']
		
		banner.save()
		messages.success(request, f'Banner "{banner.name}" updated successfully!')
		return redirect('dashboard:admin_banners')
	
	context = {
		'banner': banner,
		'position_choices': PromotionalBanner.POSITION_CHOICES,
		'title': f'Edit Banner: {banner.name}',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/banner_form.html', context)


@admin_required
def admin_banner_delete(request, banner_id):
	"""Delete a promotional banner."""
	banner = get_object_or_404(PromotionalBanner, id=banner_id)
	
	if request.method == 'POST':
		name = banner.name
		banner.delete()
		messages.success(request, f'Banner "{name}" deleted successfully!')
	
	return redirect('dashboard:admin_banners')


# ============================================
# SITE SETTINGS MANAGEMENT
# ============================================

@admin_required
def admin_site_settings(request):
	"""Edit site settings."""
	settings = SiteSettings.get_settings()
	
	if request.method == 'POST':
		settings.site_name = request.POST.get('site_name', settings.site_name)
		settings.site_tagline = request.POST.get('site_tagline', settings.site_tagline)
		settings.site_description = request.POST.get('site_description', '')
		settings.contact_email = request.POST.get('contact_email', settings.contact_email)
		settings.contact_phone = request.POST.get('contact_phone', settings.contact_phone)
		settings.contact_address = request.POST.get('contact_address', '')
		settings.facebook_url = request.POST.get('facebook_url', '')
		settings.instagram_url = request.POST.get('instagram_url', '')
		settings.twitter_url = request.POST.get('twitter_url', '')
		settings.tiktok_url = request.POST.get('tiktok_url', '')
		settings.whatsapp_number = request.POST.get('whatsapp_number', '')
		settings.business_hours = request.POST.get('business_hours', settings.business_hours)
		settings.footer_text = request.POST.get('footer_text', '')
		settings.copyright_text = request.POST.get('copyright_text', settings.copyright_text)
		settings.google_analytics_id = request.POST.get('google_analytics_id', '')
		settings.save()
		
		messages.success(request, 'Site settings updated successfully!')
		return redirect('dashboard:admin_site_settings')
	
	context = {
		'settings': settings,
		'title': 'Site Settings',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/site_settings.html', context)


# ============================================
# PAGE CONTENT MANAGEMENT
# ============================================

@admin_required
def admin_pages(request):
	"""List all page contents."""
	pages = PageContent.objects.all().order_by('page')
	
	context = {
		'pages': pages,
		'page_choices': PageContent.PAGE_CHOICES,
		'title': 'Static Pages',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/pages.html', context)


@admin_required
def admin_page_add(request):
	"""Add a new page content."""
	if request.method == 'POST':
		page_type = request.POST.get('page')
		
		# Check if page already exists
		if PageContent.objects.filter(page=page_type).exists():
			messages.error(request, f'Page "{page_type}" already exists!')
			return redirect('dashboard:admin_pages')
		
		page = PageContent(
			page=page_type,
			title=request.POST.get('title'),
			content=request.POST.get('content', ''),
			meta_title=request.POST.get('meta_title', ''),
			meta_description=request.POST.get('meta_description', ''),
		)
		page.save()
		messages.success(request, f'Page "{page.get_page_display()}" created successfully!')
		return redirect('dashboard:admin_pages')
	
	# Get available page types (not yet created)
	existing_pages = PageContent.objects.values_list('page', flat=True)
	available_pages = [(k, v) for k, v in PageContent.PAGE_CHOICES if k not in existing_pages]
	
	context = {
		'page_choices': available_pages,
		'title': 'Add Page',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/page_form.html', context)


@admin_required
def admin_page_edit(request, page_slug):
	"""Edit a page content."""
	page = get_object_or_404(PageContent, page=page_slug)
	
	if request.method == 'POST':
		page.title = request.POST.get('title', page.title)
		page.content = request.POST.get('content', '')
		page.meta_title = request.POST.get('meta_title', '')
		page.meta_description = request.POST.get('meta_description', '')
		page.save()
		
		messages.success(request, f'Page "{page.get_page_display()}" updated successfully!')
		return redirect('dashboard:admin_pages')
	
	context = {
		'page': page,
		'page_choices': PageContent.PAGE_CHOICES,
		'title': f'Edit Page: {page.get_page_display()}',
		'admin_active': 'content',
		**get_admin_sidebar_context(),
	}
	return render(request, 'dashboard/admin/page_form.html', context)


@admin_required
def admin_page_delete(request, page_slug):
	"""Delete a page content."""
	page = get_object_or_404(PageContent, page=page_slug)
	
	if request.method == 'POST':
		title = page.get_page_display()
		page.delete()
		messages.success(request, f'Page "{title}" deleted successfully!')
	
	return redirect('dashboard:admin_pages')


@customer_required
def customer_cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' and order.can_cancel:
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.order_number} has been cancelled.')
    else:
        messages.error(request, 'Unable to cancel this order.')
    return redirect('dashboard:customer_orders')

@customer_required
def customer_delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' and order.status == 'cancelled':
        order.delete()
        messages.success(request, f'Order #{order.order_number} has been deleted.')
    else:
        messages.error(request, 'You can only delete cancelled orders.')
    return redirect('dashboard:customer_orders')
