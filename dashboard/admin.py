from django.contrib import admin
from django.utils import timezone
from django.urls import path
from django.shortcuts import render

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
