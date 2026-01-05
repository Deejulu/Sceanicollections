"""
URL configuration for aniscents project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from .views import home, about_page, contact_page, faq_page, privacy_page, terms_page, shipping_page, returns_page, tutorial_page, debug_test_view

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', home, name='home'),

    # Debug test view
    path('debug-test/', debug_test_view, name='debug_test'),

    # Static Pages
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('faq/', faq_page, name='faq'),
    path('privacy/', privacy_page, name='privacy'),
    path('terms/', terms_page, name='terms'),
    path('shipping/', shipping_page, name='shipping'),
    path('returns/', returns_page, name='returns'),
    path('how-to-shop/', tutorial_page, name='tutorial'),

    # Store
    path('store/', include('store.urls')),

    # Cart
    path('cart/', include('cart.urls')),

    # Orders
    path('orders/', include('orders.urls')),

    # Dashboard
    path('dashboard/', include('dashboard.urls')),

    # Accounts (Custom)
    path('accounts/', include('accounts.urls')),

    # Feedback
    path('feedback/', include('feedback.urls')),

    # Reviews
    path('reviews/', include('reviews.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
