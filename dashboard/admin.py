from django.contrib import admin
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from orders.models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ['order_number', 'customer_email', 'status', 'total', 'created_at']
	list_filter = ['status', 'payment_status', 'created_at']
	search_fields = ['order_number', 'customer_email', 'customer_phone']
	readonly_fields = ['created_at', 'updated_at']
	actions = ['mark_as_shipped', 'mark_as_delivered']
    
	def mark_as_shipped(self, request, queryset):
		queryset.update(status='shipped')
		self.message_user(request, f"{queryset.count()} orders marked as shipped")
    
	def mark_as_delivered(self, request, queryset):
		queryset.update(status='delivered', delivered_at=timezone.now())
		self.message_user(request, f"{queryset.count()} orders marked as delivered")

# Create custom admin site
class SceaniCollectionsAdminSite(admin.AdminSite):
	site_header = "SceaniCollections Admin"
	site_title = "SceaniCollections Admin Portal"
	index_title = "Welcome to SceaniCollections Admin"
    
	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
			path('reports/', self.admin_view(self.reports_view), name='reports'),
		]
		return custom_urls + urls
    
	def analytics_view(self, request):
		# Add analytics logic
		return render(request, 'admin/analytics.html')
