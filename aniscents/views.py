from django.http import HttpResponse

# Debug test view
def debug_test_view(request):
    return HttpResponse("Debug test view is working!")
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from store.models import Product, Category
from store.cms_models import PageContent

def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    new_arrivals = Product.objects.filter(is_new=True, is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(request, 'pages/index.html', {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
    })


def page_view(request, page_slug):
    """View for static pages managed via CMS."""
    try:
        page_content = PageContent.objects.get(page=page_slug)
    except PageContent.DoesNotExist:
        page_content = None
    
    context = {
        'page': page_content,
        'page_slug': page_slug,
    }
    
    # Use specific templates if they exist, otherwise use generic
    template_name = f'pages/{page_slug}.html'
    return render(request, template_name, context)


def about_page(request):
    """About Us page."""
    return page_view(request, 'about')


def contact_page(request):
    """Contact Us page."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not all([name, email, subject, message]):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please fill in all fields.'}, status=400)
            from django.contrib import messages
            messages.error(request, 'Please fill in all fields.')
        else:
            # Send email
            from accounts.utils import send_contact_form_email
            send_contact_form_email(name, email, subject, message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Thank you for your message! We\'ll get back to you soon.'})
            from django.contrib import messages
            messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
    
    return page_view(request, 'contact')


def faq_page(request):
    """FAQ page."""
    return page_view(request, 'faq')


def privacy_page(request):
    """Privacy Policy page."""
    return page_view(request, 'privacy')


def terms_page(request):
    """Terms & Conditions page."""
    return page_view(request, 'terms')


def shipping_page(request):
    """Shipping Policy page."""
    return page_view(request, 'shipping')


def returns_page(request):
    """Returns Policy page."""
    return page_view(request, 'returns')


def tutorial_page(request):
    """Tutorial/How to Shop page."""
    return render(request, 'pages/tutorial.html')
