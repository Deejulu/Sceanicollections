from django.db import models
from django.conf import settings
from django.utils import timezone

class AdminDashboard(models.Model):
    """Admin dashboard settings and preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='admin_dashboard'
    )
    # Dashboard preferences
    default_view = models.CharField(
        max_length=50, 
        default='overview',
        choices=[
            ('overview', 'Overview'),
            ('orders', 'Orders'),
            ('products', 'Products'),
            ('customers', 'Customers'),
            ('analytics', 'Analytics'),
        ]
    )
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    new_order_notifications = models.BooleanField(default=True)
    low_stock_notifications = models.BooleanField(default=True)
    review_notifications = models.BooleanField(default=True)
    # Display preferences
    items_per_page = models.IntegerField(default=20)
    show_charts = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    # Recent activity
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Admin Dashboard for {self.user.email}"
    def update_activity(self, ip_address=None):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.save()

class DashboardWidget(models.Model):
    """Customizable dashboard widgets."""
    WIDGET_TYPE_CHOICES = (
        ('stat', 'Statistic'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('list', 'List'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboard_widgets'
    )
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    data_source = models.CharField(max_length=100, help_text="Source of data for widget")
    # Display properties
    column = models.IntegerField(default=1)
    row = models.IntegerField(default=1)
    width = models.IntegerField(default=1, help_text="Number of columns widget spans (1-4)")
    height = models.IntegerField(default=1, help_text="Number of rows widget spans (1-4)")
    # Settings
    refresh_interval = models.IntegerField(default=300, help_text="Refresh interval in seconds")
    is_visible = models.BooleanField(default=True)
    # Custom filters/settings
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['column', 'row']
    def __str__(self):
        return f"{self.title} - {self.user.email}"

class AdminNotification(models.Model):
    """Notifications for admin users."""
    NOTIFICATION_TYPE_CHOICES = (
        ('order', 'New Order'),
        ('review', 'New Review'),
        ('inventory', 'Low Inventory'),
        ('customer', 'Customer Support'),
        ('system', 'System Alert'),
        ('payment', 'Payment Received'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='admin_notifications',
        limit_choices_to={'user_type__in': ['admin', 'staff']}
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    # Status
    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=True)
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"
    def mark_as_read(self, user):
        """Mark notification as read for specific user."""
        from django.db.models import Q
        # Check if this user was targeted
        if self.users.filter(id=user.id).exists():
            # Create a through model or mark as read for all
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    @classmethod
    def create_order_notification(cls, order, users=None):
        """Create notification for new order."""
        from accounts.models import User
        if users is None:
            users = User.objects.filter(
                user_type__in=['admin', 'staff'],
                is_active=True
            )
        notification = cls.objects.create(
            notification_type='order',
            priority='high' if order.total > 50000 else 'medium',
            title=f"New Order #{order.order_number}",
            message=f"New order received from {order.customer_name} for ₦{order.total:,.2f}",
            data={
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_email': order.customer_email,
                'total_amount': str(order.total),
            },
            action_url=f"/admin/orders/order/{order.id}/change/",
            action_label="View Order"
        )
        notification.users.set(users)
        return notification
    @classmethod
    def create_inventory_notification(cls, product, users=None):
        """Create notification for low inventory."""
        from accounts.models import User
        if users is None:
            users = User.objects.filter(
                user_type__in=['admin', 'staff'],
                is_active=True
            )
        notification = cls.objects.create(
            notification_type='inventory',
            priority='medium',
            title=f"Low Inventory: {product.name}",
            message=f"{product.name} is running low. Current stock: {product.stock_quantity}",
            data={
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': product.stock_quantity,
                'low_stock_threshold': product.low_stock_threshold,
            },
            action_url=f"/admin/store/product/{product.id}/change/",
            action_label="Update Inventory"
        )
        notification.users.set(users)
        return notification

class CustomerDashboard(models.Model):
    """Customer dashboard settings and preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_dashboard'
    )
    # Dashboard preferences
    show_recent_orders = models.BooleanField(default=True)
    show_wishlist = models.BooleanField(default=True)
    show_recommendations = models.BooleanField(default=True)
    show_loyalty_points = models.BooleanField(default=True)
    # Notification preferences
    order_updates_email = models.BooleanField(default=True)
    order_updates_sms = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=True)
    review_reminders = models.BooleanField(default=True)
    # Privacy settings
    show_purchase_history = models.BooleanField(default=True)
    allow_profile_view = models.BooleanField(default=False)
    # Activity tracking
    last_viewed_products = models.JSONField(default=list, blank=True)
    recently_searched = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Customer Dashboard for {self.user.email}"
    def add_viewed_product(self, product):
        """Add product to recently viewed."""
        from django.core import serializers
        product_data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'image': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else '',
            'price': str(product.price),
            'viewed_at': timezone.now().isoformat(),
        }
        viewed = self.last_viewed_products
        # Remove if already exists
        viewed = [p for p in viewed if p['id'] != product.id]
        # Add to beginning
        viewed.insert(0, product_data)
        # Keep only last 20
        self.last_viewed_products = viewed[:20]
        self.save()
    def add_search_term(self, term):
        """Add search term to recently searched."""
        if not term or len(term.strip()) < 2:
            return
        searched = self.recently_searched
        # Remove if already exists
        searched = [t for t in searched if t.lower() != term.lower()]
        # Add to beginning
        searched.insert(0, term.strip())
        # Keep only last 10
        self.recently_searched = searched[:10]
        self.save()

class CustomerNotification(models.Model):
    """Notifications for customers."""
    NOTIFICATION_TYPE_CHOICES = (
        ('order', 'Order Update'),
        ('shipment', 'Shipment Update'),
        ('wishlist', 'Wishlist Update'),
        ('price_drop', 'Price Drop'),
        ('back_in_stock', 'Back in Stock'),
        ('review', 'Review Reminder'),
        ('loyalty', 'Loyalty Points'),
        ('marketing', 'Marketing'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    # Delivery methods
    sent_email = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)
    sent_push = models.BooleanField(default=False)
    in_app = models.BooleanField(default=True)
    # Status
    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=True)
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    def mark_as_sent(self, method='email'):
        """Mark notification as sent via specified method."""
        if method == 'email':
            self.sent_email = True
        elif method == 'sms':
            self.sent_sms = True
        elif method == 'push':
            self.sent_push = True
        if not self.sent_at:
            self.sent_at = timezone.now()
        self.save()
    @classmethod
    def create_order_status_notification(cls, order, status):
        """Create notification for order status update."""
        status_messages = {
            'confirmed': f"Your order #{order.order_number} has been confirmed and is being processed.",
            'processing': f"Your order #{order.order_number} is now being processed.",
            'shipped': f"Your order #{order.order_number} has been shipped! Tracking: {order.tracking_number or 'Will be updated soon'}",
            'delivered': f"Your order #{order.order_number} has been delivered. We hope you love your purchase!",
        }
        if status not in status_messages:
            return None
        notification = cls.objects.create(
            user=order.user,
            notification_type='order',
            title=f"Order #{order.order_number} Update",
            message=status_messages[status],
            data={
                'order_id': order.id,
                'order_number': order.order_number,
                'status': status,
                'tracking_number': order.tracking_number,
            },
            action_url=order.get_absolute_url(),
            action_label="View Order"
        )
        return notification
    @classmethod
    def create_price_drop_notification(cls, user, product, old_price, new_price):
        """Create notification for price drop."""
        discount = ((old_price - new_price) / old_price) * 100
        notification = cls.objects.create(
            user=user,
            notification_type='price_drop',
            title=f"Price Drop! {product.name}",
            message=f"{product.name} price has dropped by {discount:.0f}%! Now ₦{new_price:,.2f} (was ₦{old_price:,.2f})",
            data={
                'product_id': product.id,
                'product_name': product.name,
                'old_price': str(old_price),
                'new_price': str(new_price),
                'discount_percentage': round(discount, 2),
            },
            action_url=product.get_absolute_url(),
            action_label="Shop Now"
        )
        return notification

class AnalyticsData(models.Model):
    """Stored analytics data for dashboards."""
    DATA_TYPE_CHOICES = (
        ('sales', 'Sales'),
        ('orders', 'Orders'),
        ('customers', 'Customers'),
        ('products', 'Products'),
        ('traffic', 'Website Traffic'),
        ('revenue', 'Revenue'),
    )
    PERIOD_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    date = models.DateField()
    # Metrics
    value = models.DecimalField(max_digits=15, decimal_places=2)
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    target_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Breakdown
    breakdown = models.JSONField(default=dict, blank=True)
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    is_final = models.BooleanField(default=True)
    class Meta:
        unique_together = ['data_type', 'period', 'date']
        ordering = ['-date', 'data_type']
    def __str__(self):
        return f"{self.get_data_type_display()} - {self.date} ({self.get_period_display()})"
    @property
    def growth_rate(self):
        """Calculate growth rate compared to previous period."""
        if self.previous_value and self.previous_value > 0:
            return ((self.value - self.previous_value) / self.previous_value) * 100
        return None
    @classmethod
    def update_sales_data(cls, date=None):
        """Update sales analytics data."""
        from orders.models import Order
        from django.db.models import Sum, Count
        from django.utils import timezone
        if date is None:
            date = timezone.now().date()
        # Daily sales
        daily_sales = Order.objects.filter(
            created_at__date=date,
            payment_status='paid'
        ).aggregate(
            total_sales=Sum('total'),
            order_count=Count('id')
        )
        cls.objects.update_or_create(
            data_type='sales',
            period='daily',
            date=date,
            defaults={
                'value': daily_sales['total_sales'] or 0,
                'breakdown': {
                    'order_count': daily_sales['order_count'] or 0,
                    'average_order_value': (daily_sales['total_sales'] or 0) / (daily_sales['order_count'] or 1)
                }
            }
        )
        # Monthly sales
        monthly_sales = Order.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month,
            payment_status='paid'
        ).aggregate(
            total_sales=Sum('total'),
            order_count=Count('id')
        )
        cls.objects.update_or_create(
            data_type='sales',
            period='monthly',
            date=date.replace(day=1),
            defaults={
                'value': monthly_sales['total_sales'] or 0,
                'breakdown': {
                    'order_count': monthly_sales['order_count'] or 0,
                    'average_order_value': (monthly_sales['total_sales'] or 0) / (monthly_sales['order_count'] or 1)
                }
            }
        )
