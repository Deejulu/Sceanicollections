
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from store.management.commands.populate_sample_data import Command as PopulateSampleDataCommand


@staff_member_required
def populate_sample_data_view(request):
	error = None
	if request.method == 'POST':
		try:
			cmd = PopulateSampleDataCommand()
			cmd.handle()
			messages.success(request, 'Sample categories and products have been populated!')
			return redirect(request.path)
		except Exception as e:
			error = str(e)
			messages.error(request, f"Error populating sample data: {error}")
	return render(request, 'admin/populate_sample_data.html', {'error': error})

class CustomAdminSite(admin.AdminSite):
	site_header = 'AniScents Administration'
	site_title = 'AniScents Admin'
	index_title = 'Site Administration'

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('populate-sample-data/', self.admin_view(populate_sample_data_view), name='populate_sample_data'),
		]
		return custom_urls + urls

custom_admin_site = CustomAdminSite(name='custom_admin')
