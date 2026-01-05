
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Product, Category
from .cms_models import ShopPageContent

def category_list(request):
	categories = Category.objects.filter(is_active=True)
	return render(request, 'store/category_list.html', {'categories': categories})

def category_detail(request, slug):
	category = get_object_or_404(Category, slug=slug, is_active=True)
	products = Product.objects.filter(category=category, is_available=True)
	return render(request, 'store/category_detail.html', {'category': category, 'products': products})

class ProductListView(ListView):
	"""View for listing all products with filters."""
	model = Product
	template_name = 'store/product_list.html'
	context_object_name = 'products'
	paginate_by = 12
	def get_queryset(self):
		from django.db.models import Q
		queryset = Product.objects.filter(is_available=True)
		# Filter by category
		category_slug = self.kwargs.get('category_slug')
		if category_slug:
			category = get_object_or_404(Category, slug=category_slug, is_active=True)
			queryset = queryset.filter(category=category)
		# Filter by price range
		min_price = self.request.GET.get('min_price')
		max_price = self.request.GET.get('max_price')
		if min_price:
			queryset = queryset.filter(price__gte=float(min_price))
		if max_price:
			queryset = queryset.filter(price__lte=float(max_price))
		# Search
		search_query = self.request.GET.get('q')
		if search_query:
			queryset = queryset.filter(
				Q(name__icontains=search_query) |
				Q(description__icontains=search_query) |
				Q(top_notes__icontains=search_query) |
				Q(heart_notes__icontains=search_query) |
				Q(base_notes__icontains=search_query)
			)
		# Sort by
		sort_by = self.request.GET.get('sort_by', 'newest')
		if sort_by == 'price_low':
			queryset = queryset.order_by('price')
		elif sort_by == 'price_high':
			queryset = queryset.order_by('-price')
		elif sort_by == 'name':
			queryset = queryset.order_by('name')
		else:  # newest
			queryset = queryset.order_by('-created_at')
		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.filter(is_active=True)
		context['selected_category'] = self.kwargs.get('category_slug', '')
		# Get filter parameters
		context['min_price'] = self.request.GET.get('min_price', '')
		context['max_price'] = self.request.GET.get('max_price', '')
		context['search_query'] = self.request.GET.get('q', '')
		context['sort_by'] = self.request.GET.get('sort_by', 'newest')
		# Add concentration and gender choices to context
		from .models import Product
		context['concentration_choices'] = Product.CONCENTRATION_CHOICES
		context['gender_choices'] = Product.GENDER_CHOICES
		# Add shop page CMS content
		context['shop_content'] = ShopPageContent.get_content()
		return context

class ProductDetailView(DetailView):
	model = Product
	template_name = 'store/product_detail.html'
	context_object_name = 'product'
	slug_field = 'slug'
	slug_url_kwarg = 'slug'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		product = self.get_object()
		# Increment view count
		product.view_count += 1
		product.save(update_fields=['view_count'])
		# Related products (same category)
		related_products = Product.objects.filter(
			category=product.category,
			is_available=True
		).exclude(id=product.id)[:4]
		# Scent notes as lists
		if product.top_notes:
			context['top_notes_list'] = [note.strip() for note in product.top_notes.split(',')]
		if product.heart_notes:
			context['heart_notes_list'] = [note.strip() for note in product.heart_notes.split(',')]
		if product.base_notes:
			context['base_notes_list'] = [note.strip() for note in product.base_notes.split(',')]
		context['related_products'] = related_products
		
		# Reviews data
		from reviews.models import Review
		reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
		
		# Rating breakdown for display
		rating_breakdown = {}
		total = reviews.count()
		for i in range(1, 6):
			count = reviews.filter(rating=i).count()
			rating_breakdown[i] = {
				'count': count,
				'percentage': round((count / total * 100) if total > 0 else 0)
			}
		context['reviews'] = reviews[:5]  # First 5 reviews
		context['rating_breakdown'] = rating_breakdown
		
		# Check if current user has already reviewed
		if self.request.user.is_authenticated:
			context['user_has_reviewed'] = Review.objects.filter(
				product=product, 
				user=self.request.user
			).exists()
		
		return context

def search(request):
	from django.db.models import Q
	query = request.GET.get('q', '')
	if query:
		products = Product.objects.filter(
			Q(name__icontains=query) |
			Q(description__icontains=query) |
			Q(top_notes__icontains=query) |
			Q(heart_notes__icontains=query) |
			Q(base_notes__icontains=query),
			is_available=True
		).order_by('-created_at')
	else:
		products = Product.objects.filter(is_available=True).order_by('-created_at')
	# Pagination
	from django.core.paginator import Paginator
	paginator = Paginator(products, 12)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'products': page_obj,
		'query': query,
		'title': f'Search Results for "{query}"' if query else 'Search Products',
	}
	return render(request, 'store/search_results.html', context)


def newsletter_subscribe(request):
	"""Handle newsletter subscription."""
	from django.http import JsonResponse
	from django.views.decorators.http import require_POST
	from .cms_models import NewsletterSubscriber
	
	if request.method != 'POST':
		return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
	
	email = request.POST.get('email', '').strip().lower()
	name = request.POST.get('name', '').strip()
	source = request.POST.get('source', 'footer')
	
	if not email:
		return JsonResponse({'success': False, 'message': 'Please enter your email address.'}, status=400)
	
	# Validate email format
	import re
	if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
		return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)
	
	# Check if already subscribed
	try:
		subscriber = NewsletterSubscriber.objects.get(email=email)
		if subscriber.is_active:
			return JsonResponse({'success': False, 'message': 'This email is already subscribed!'}, status=400)
		else:
			# Reactivate subscription
			subscriber.is_active = True
			subscriber.unsubscribed_at = None
			subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
			return JsonResponse({
				'success': True, 
				'message': 'Welcome back! Your subscription has been reactivated.'
			})
	except NewsletterSubscriber.DoesNotExist:
		pass
	
	# Create new subscriber
	subscriber = NewsletterSubscriber.objects.create(
		email=email,
		name=name,
		source=source
	)
	
	# Send welcome email
	from accounts.utils import send_newsletter_welcome_email
	send_newsletter_welcome_email(email, subscriber.unsubscribe_token)
	
	return JsonResponse({
		'success': True,
		'message': 'Thank you for subscribing! Check your email for a special welcome offer.'
	})


def newsletter_unsubscribe(request):
	"""Handle newsletter unsubscription."""
	from .cms_models import NewsletterSubscriber
	
	token = request.GET.get('token', '')
	
	if not token:
		context = {'message': 'Invalid unsubscribe link.', 'success': False}
		return render(request, 'store/newsletter_unsubscribe.html', context)
	
	try:
		subscriber = NewsletterSubscriber.objects.get(unsubscribe_token=token)
		if subscriber.is_active:
			subscriber.unsubscribe()
			context = {'message': 'You have been successfully unsubscribed.', 'success': True, 'email': subscriber.email}
		else:
			context = {'message': 'This email is already unsubscribed.', 'success': True, 'email': subscriber.email}
	except NewsletterSubscriber.DoesNotExist:
		context = {'message': 'Invalid unsubscribe link.', 'success': False}
	
	return render(request, 'store/newsletter_unsubscribe.html', context)
