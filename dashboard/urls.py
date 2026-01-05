from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from . import views

app_name = 'dashboard'

@login_required
def dashboard_redirect(request):
    """Redirect user to appropriate dashboard based on user type."""
    if request.user.is_admin_user():
        return redirect('dashboard:admin_dashboard')
    else:
        return redirect('dashboard:customer_dashboard')

urlpatterns = [
    # Root dashboard redirect
    path('', dashboard_redirect, name='dashboard_redirect'),
    
    # Customer Dashboard
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/orders/', views.customer_orders, name='customer_orders'),
    path('customer/orders/<int:order_id>/cancel/', views.customer_cancel_order, name='customer_cancel_order'),
    path('customer/orders/<int:order_id>/delete/', views.customer_delete_order, name='customer_delete_order'),
    path('customer/wishlist/', views.customer_wishlist, name='customer_wishlist'),
    path('customer/wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('customer/wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('customer/wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('customer/profile/', views.customer_profile, name='customer_profile'),
    path('customer/addresses/', views.customer_addresses, name='customer_addresses'),
    
    # Admin Dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin/orders/<int:order_id>/payment/', views.admin_update_payment_status, name='admin_update_payment_status'),
    path('admin/orders/<int:order_id>/notes/', views.admin_update_order_notes, name='admin_update_order_notes'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/<int:product_id>/stock/', views.admin_update_stock, name='admin_update_stock'),
    path('admin/customers/', views.admin_customers, name='admin_customers'),
    path('admin/customers/<int:customer_id>/', views.admin_customer_detail, name='admin_customer_detail'),
    path('admin/customers/<int:customer_id>/toggle-status/', views.admin_toggle_customer_status, name='admin_toggle_customer_status'),
    path('admin/feedback/', views.admin_feedback, name='admin_feedback'),
    path('admin/feedback/<int:feedback_id>/status/', views.admin_feedback_status, name='admin_feedback_status'),
    path('admin/feedback/<int:feedback_id>/respond/', views.admin_feedback_respond, name='admin_feedback_respond'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/settings/profile/', views.admin_update_profile, name='admin_update_profile'),
    path('admin/settings/password/', views.admin_change_password, name='admin_change_password'),
    
    # Content Management
    path('admin/content/', views.admin_site_content, name='admin_site_content'),
    path('admin/content/shop/', views.admin_shop_content, name='admin_shop_content'),
    path('admin/content/hero/', views.admin_hero_section, name='admin_hero_section'),
    path('admin/content/site-settings/', views.admin_site_settings, name='admin_site_settings'),
    
    # Categories Management
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('admin/categories/<int:category_id>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    # Products Management (Add/Edit/Delete)
    path('admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/products/<int:product_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin/products/image/<int:image_id>/delete/', views.admin_product_image_delete, name='admin_product_image_delete'),
    
    # Homepage Sections Management
    path('admin/content/sections/', views.admin_homepage_sections, name='admin_homepage_sections'),
    path('admin/content/sections/add/', views.admin_homepage_section_add, name='admin_homepage_section_add'),
    path('admin/content/sections/<int:section_id>/edit/', views.admin_homepage_section_edit, name='admin_homepage_section_edit'),
    path('admin/content/sections/<int:section_id>/delete/', views.admin_homepage_section_delete, name='admin_homepage_section_delete'),
    
    # Banners Management
    path('admin/content/banners/', views.admin_banners, name='admin_banners'),
    path('admin/content/banners/add/', views.admin_banner_add, name='admin_banner_add'),
    path('admin/content/banners/<int:banner_id>/edit/', views.admin_banner_edit, name='admin_banner_edit'),
    path('admin/content/banners/<int:banner_id>/delete/', views.admin_banner_delete, name='admin_banner_delete'),
    
    # Static Pages Management
    path('admin/content/pages/', views.admin_pages, name='admin_pages'),
    path('admin/content/pages/add/', views.admin_page_add, name='admin_page_add'),
    path('admin/content/pages/<str:page_slug>/edit/', views.admin_page_edit, name='admin_page_edit'),
    path('admin/content/pages/<str:page_slug>/delete/', views.admin_page_delete, name='admin_page_delete'),
]
