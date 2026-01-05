from django.contrib import admin
from .models import Order, OrderItem, Payment, OrderNote

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_email', 'status', 'payment_status', 'total', 'created_at')
    search_fields = ('order_number', 'customer_email', 'customer_phone')
    list_filter = ('status', 'payment_status', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = []

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'unit_price', 'quantity', 'total', 'created_at')
    search_fields = ('order__order_number', 'product_name')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_gateway', 'amount', 'currency', 'status', 'created_at')
    search_fields = ('order__order_number', 'gateway_reference', 'bank_name', 'account_number')
    list_filter = ('payment_gateway', 'status', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'note_type', 'author', 'is_visible_to_customer', 'created_at')
    search_fields = ('order__order_number', 'author__email', 'content')
    list_filter = ('note_type', 'is_visible_to_customer', 'created_at')
    date_hierarchy = 'created_at'
