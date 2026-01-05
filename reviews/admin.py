from django.contrib import admin
from .models import Review, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'verified_purchase', 'is_approved', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_approved', 'verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'title', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['helpful_count', 'verified_purchase', 'created_at', 'updated_at']
    raw_id_fields = ['product', 'user']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'is_approved')
        }),
        ('Rating', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Perfume-specific Ratings', {
            'fields': ('longevity_rating', 'sillage_rating', 'value_rating'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('helpful_count', 'verified_purchase', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Update product rating when review is saved
        obj.product.update_rating()


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['review', 'user']
