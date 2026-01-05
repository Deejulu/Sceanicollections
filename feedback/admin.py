from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'get_customer', 
        'feedback_type', 
        'display_rating',
        'subject_preview',
        'status_badge', 
        'order_link',
        'created_at'
    ]
    list_filter = ['status', 'feedback_type', 'rating', 'created_at']
    search_fields = ['customer_name', 'customer_email', 'user__email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'user', 'order']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'customer_name', 'customer_email', 'order')
        }),
        ('Feedback Details', {
            'fields': ('feedback_type', 'rating', 'subject', 'message')
        }),
        ('Admin Response', {
            'fields': ('status', 'admin_notes', 'admin_response', 'responded_by', 'responded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_resolved']
    
    def get_customer(self, obj):
        if obj.user:
            return obj.user.email
        return obj.customer_email or obj.customer_name or "Anonymous"
    get_customer.short_description = 'Customer'
    
    def display_rating(self, obj):
        if not obj.rating:
            return "-"
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        color = "#FFD700" if obj.rating >= 4 else "#FFA500" if obj.rating == 3 else "#FF6B6B"
        return format_html(
            '<span style="color: {}; font-size: 14px;">{}</span>',
            color, stars
        )
    display_rating.short_description = 'Rating'
    
    def subject_preview(self, obj):
        if obj.subject:
            return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    subject_preview.short_description = 'Preview'
    
    def status_badge(self, obj):
        colors = {
            'new': '#EF4444',       # Red
            'read': '#3B82F6',      # Blue
            'responded': '#F59E0B', # Amber
            'resolved': '#10B981',  # Green
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            colors.get(obj.status, '#6B7280'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def order_link(self, obj):
        if obj.order:
            return format_html(
                '<a href="/admin/orders/order/{}/change/" style="color: #1a237e;">{}</a>',
                obj.order.id,
                obj.order.order_number
            )
        return "-"
    order_link.short_description = 'Order'
    
    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
        self.message_user(request, f"{queryset.count()} feedback(s) marked as read.")
    mark_as_read.short_description = "Mark selected as Read"
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
        self.message_user(request, f"{queryset.count()} feedback(s) marked as resolved.")
    mark_as_resolved.short_description = "Mark selected as Resolved"
    
    def save_model(self, request, obj, form, change):
        # Auto-set responded_by and responded_at when admin response is added
        if obj.admin_response and not obj.responded_at:
            obj.responded_by = request.user
            obj.responded_at = timezone.now()
            if obj.status == 'new' or obj.status == 'read':
                obj.status = 'responded'
        super().save_model(request, obj, form, change)
