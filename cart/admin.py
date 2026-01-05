from django.contrib import admin
from .models import Cart, CartItem, Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin for Coupon model."""
    list_display = ('code', 'discount_display', 'is_active', 'times_used', 'max_uses', 'valid_from', 'valid_until')
    list_filter = ('is_active', 'discount_type', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('times_used', 'created_at', 'updated_at')
    filter_horizontal = ('specific_products', 'specific_categories')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value', 'max_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('min_purchase_amount', 'max_uses', 'max_uses_per_user', 'times_used')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Targeting', {
            'fields': ('first_order_only', 'specific_products', 'specific_categories'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def discount_display(self, obj):
        return obj.get_discount_display()
    discount_display.short_description = 'Discount'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    """Admin for CouponUsage model."""
    list_display = ('coupon', 'user', 'order', 'used_at')
    list_filter = ('used_at', 'coupon')
    search_fields = ('coupon__code', 'user__email')
    raw_id_fields = ('coupon', 'user', 'order')
    readonly_fields = ('used_at',)

class CartItemInline(admin.TabularInline):
    """Inline for cart items."""
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'total_price', 'added_at')
    can_delete = False
    def unit_price(self, obj):
        return obj.unit_price
    unit_price.short_description = 'Unit Price'
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Total'

class CartAdmin(admin.ModelAdmin):
    """Admin for Cart model."""
    list_display = ('id', 'user_info', 'session_key', 'total_items', 'subtotal', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('session_key', 'created_at', 'updated_at', 'subtotal', 'total_items')
    inlines = [CartItemInline]
    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'session_key', 'abandoned_at')
        }),
        ('Cart Options', {
            'fields': ('gift_wrapping', 'gift_message', 'gift_recipient_name', 'gift_recipient_email'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    def user_info(self, obj):
        if obj.user:
            return f"{obj.user.email} ({obj.user.get_full_name()})"
        return "Anonymous"
    user_info.short_description = 'User'
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Items'
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'

class CartItemAdmin(admin.ModelAdmin):
    """Admin for CartItem model."""
    list_display = ('id', 'cart_info', 'product_name', 'quantity', 'unit_price', 'total_price', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('cart', 'product', 'quantity', 'unit_price', 'total_price', 'added_at')
    def cart_info(self, obj):
        if obj.cart.user:
            return f"Cart #{obj.cart.id} - {obj.cart.user.email}"
        return f"Cart #{obj.cart.id} (Anonymous)"
    cart_info.short_description = 'Cart'
    def product_name(self, obj):
        return obj.product_name
    product_name.short_description = 'Product'
    def unit_price(self, obj):
        return obj.unit_price
    unit_price.short_description = 'Unit Price'
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Total'

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
