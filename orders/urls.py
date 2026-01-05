from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Payment gateway routes
    path('pay/paystack/<int:order_id>/', views.initiate_paystack, name='initiate_paystack'),
    path('pay/paystack/callback/', views.paystack_callback, name='paystack_callback'),
    path('pay/flutterwave/<int:order_id>/', views.initiate_flutterwave, name='initiate_flutterwave'),
    path('pay/flutterwave/callback/', views.flutterwave_callback, name='flutterwave_callback'),
]
