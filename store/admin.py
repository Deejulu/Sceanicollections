from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, PaymentMethod
# PaymentMethod admin
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'display_order', 'updated_at')
    list_editable = ('is_active', 'display_order')
    search_fields = ('name', 'code', 'description')
    ordering = ('display_order', 'name')
    list_filter = ('is_active',)
from .cms_models import SiteSettings, HeroSection, HomepageSection, PromotionalBanner, ShopPageContent, PageContent, NewsletterSubscriber

class ProductImageInline(admin.TabularInline):
    """Inline for product images."""
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "No image"
    image_preview.short_description = "Preview"


from django.contrib import messages
from store.management.commands.populate_sample_data import Command as PopulateSampleDataCommand

class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'concentration', 'created_at')
    search_fields = ('name', 'sku', 'short_description', 'top_notes', 'heart_notes', 'base_notes')
    list_editable = ('price', 'stock_quantity', 'is_featured')
    readonly_fields = ('created_at', 'updated_at', 'sku', 'view_count', 'purchase_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'concentration')
        }),
        ('Descriptions', {
            'fields': ('short_description', 'full_description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Scent Notes', {
            'fields': ('top_notes', 'heart_notes', 'base_notes'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_featured', 'is_bestseller'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'purchase_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ProductImageInline]
    actions = ['mark_as_featured', 'mark_as_not_featured', 'activate_products', 'deactivate_products', 'populate_sample_data']

    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured")
    mark_as_featured.short_description = "Mark selected products as featured"
    def mark_as_not_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} products marked as not featured")
    mark_as_not_featured.short_description = "Mark selected products as not featured"
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} products activated")
    activate_products.short_description = "Activate selected products"
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} products deactivated")
    deactivate_products.short_description = "Deactivate selected products"

    def populate_sample_data(self, request, queryset):
        # Call the management command logic directly
        cmd = PopulateSampleDataCommand()
        cmd.handle()
        self.message_user(request, "Sample categories and products have been populated!", level=messages.SUCCESS)
    populate_sample_data.short_description = "Populate sample categories and products"


class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    list_display = ('name', 'is_active', 'product_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    actions = ['populate_sample_data']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

    def populate_sample_data(self, request, queryset):
        cmd = PopulateSampleDataCommand()
        cmd.handle()
        self.message_user(request, "Sample categories and products have been populated!", level=messages.SUCCESS)
    populate_sample_data.short_description = "Populate sample categories and products"


# CMS Models Admin
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for Site Settings."""
    fieldsets = (
        ('Site Info', {
            'fields': ('site_name', 'site_tagline', 'site_description')
        }),
        ('Contact Info', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'tiktok_url', 'whatsapp_number')
        }),
        ('Business & Footer', {
            'fields': ('business_hours', 'footer_text', 'copyright_text')
        }),
        ('SEO', {
            'fields': ('google_analytics_id',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Allow only one instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    """Admin for Hero Section."""
    list_display = ('title_line1', 'title_line2', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    fieldsets = (
        ('Content', {
            'fields': ('badge_text', 'title_line1', 'title_line2', 'subtitle')
        }),
        ('Call to Action', {
            'fields': ('cta_primary_text', 'cta_primary_url', 'cta_secondary_text', 'cta_secondary_url')
        }),
        ('Image', {
            'fields': ('hero_image', 'hero_image_url')
        }),
        ('Stats', {
            'fields': ('stat1_value', 'stat1_label', 'stat2_value', 'stat2_label', 'stat3_value', 'stat3_label')
        }),
        ('Floating Cards', {
            'fields': ('card1_title', 'card1_subtitle', 'card1_icon', 'card2_title', 'card2_subtitle', 'card2_icon'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    """Admin for Homepage Sections."""
    list_display = ('section_type', 'title', 'display_order', 'is_active')
    list_filter = ('section_type', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(PromotionalBanner)
class PromotionalBannerAdmin(admin.ModelAdmin):
    """Admin for Promotional Banners."""
    list_display = ('name', 'position', 'is_active', 'start_date', 'end_date')
    list_filter = ('position', 'is_active')
    list_editable = ('is_active',)


@admin.register(ShopPageContent)
class ShopPageContentAdmin(admin.ModelAdmin):
    """Admin for Shop Page Content."""
    fieldsets = (
        ('Page Header', {
            'fields': ('page_title', 'page_subtitle', 'header_image')
        }),
        ('Empty State', {
            'fields': ('empty_title', 'empty_message')
        }),
        ('Filter Labels', {
            'fields': ('category_filter_label', 'price_filter_label', 'sort_label')
        }),
    )

    def has_add_permission(self, request):
        return not ShopPageContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    """Admin for Page Content."""
    list_display = ('page', 'title', 'updated_at')
    list_filter = ('page',)
    search_fields = ('title', 'content')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin for Newsletter Subscribers."""
    list_display = ('email', 'name', 'is_active', 'source', 'subscribed_at')
    list_filter = ('is_active', 'source', 'subscribed_at')
    search_fields = ('email', 'name')
    list_editable = ('is_active',)
    readonly_fields = ('unsubscribe_token', 'subscribed_at', 'unsubscribed_at')
    date_hierarchy = 'subscribed_at'
    ordering = ['-subscribed_at']
    
    actions = ['export_active_subscribers']
    
    def export_active_subscribers(self, request, queryset):
        """Export active subscribers emails."""
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="newsletter_subscribers.csv"'
        writer = csv.writer(response)
        writer.writerow(['Email', 'Name', 'Subscribed At', 'Source'])
        for subscriber in queryset.filter(is_active=True):
            writer.writerow([subscriber.email, subscriber.name, subscriber.subscribed_at, subscriber.source])
        return response
    export_active_subscribers.short_description = "Export selected subscribers to CSV"


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
