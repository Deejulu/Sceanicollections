from django.db import models
from store.models import Product
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django_countries.fields import CountryField
import uuid
from decimal import Decimal

class Order(models.Model):
	"""Main order model."""
	STATUS_CHOICES = (
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('delivered', 'Delivered'),
		('cancelled', 'Cancelled'),
		('refunded', 'Refunded'),
		('failed', 'Failed'),
	)
	PAYMENT_STATUS_CHOICES = (
		('pending', 'Pending'),
		('paid', 'Paid'),
		('partially_paid', 'Partially Paid'),
		('failed', 'Failed'),
		('refunded', 'Refunded'),
		('cancelled', 'Cancelled'),
	)
	PAYMENT_METHOD_CHOICES = (
		('paystack', 'Paystack'),
	)
	SHIPPING_METHOD_CHOICES = (
		('standard', 'Standard Delivery (3-5 days)'),
		('express', 'Express Delivery (2 days - Lagos/Benin/Warri)'),
		('pickup', 'Store Pickup'),
	)
	# Order identification
	order_number = models.CharField(max_length=20, unique=True, editable=False)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL, 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True,
		related_name='orders'
	)
	# Order status
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
	# Totals
	subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	# Payment information
	payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
	transaction_id = models.CharField(max_length=100, blank=True)
	payment_reference = models.CharField(max_length=100, blank=True)
	# Customer information (stored at time of order)
	customer_email = models.EmailField()
	customer_phone = models.CharField(max_length=20)
	customer_first_name = models.CharField(max_length=100)
	customer_last_name = models.CharField(max_length=100)
	# Shipping information
	shipping_method = models.CharField(max_length=20, choices=SHIPPING_METHOD_CHOICES, default='standard')
	shipping_full_name = models.CharField(max_length=200)
	shipping_address = models.TextField()
	shipping_city = models.CharField(max_length=100)
	shipping_state = models.CharField(max_length=100)
	shipping_postal_code = models.CharField(max_length=20)
	shipping_country = CountryField()
	shipping_phone = models.CharField(max_length=20)
	shipping_instructions = models.TextField(blank=True)
	# Billing information (if different from shipping)
	billing_same_as_shipping = models.BooleanField(default=True)
	billing_full_name = models.CharField(max_length=200, blank=True)
	billing_address = models.TextField(blank=True)
	billing_city = models.CharField(max_length=100, blank=True)
	billing_state = models.CharField(max_length=100, blank=True)
	billing_postal_code = models.CharField(max_length=20, blank=True)
	billing_country = CountryField(blank=True)
	# Gift options
	is_gift = models.BooleanField(default=False)
	gift_message = models.TextField(blank=True)
	gift_recipient_name = models.CharField(max_length=100, blank=True)
	gift_recipient_email = models.EmailField(blank=True)
	gift_wrapping = models.BooleanField(default=False)
	gift_wrapping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	# Dates
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	confirmed_at = models.DateTimeField(null=True, blank=True)
	processing_at = models.DateTimeField(null=True, blank=True)
	shipped_at = models.DateTimeField(null=True, blank=True)
	delivered_at = models.DateTimeField(null=True, blank=True)
	cancelled_at = models.DateTimeField(null=True, blank=True)
	# Shipping tracking
	tracking_number = models.CharField(max_length=100, blank=True)
	tracking_url = models.URLField(blank=True)
	carrier = models.CharField(max_length=100, blank=True)
	# Notes
	customer_notes = models.TextField(blank=True)
	internal_notes = models.TextField(blank=True)
	# Analytics
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)
	referral_source = models.CharField(max_length=200, blank=True)
	utm_source = models.CharField(max_length=100, blank=True)
	utm_medium = models.CharField(max_length=100, blank=True)
	utm_campaign = models.CharField(max_length=100, blank=True)
	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['order_number']),
			models.Index(fields=['status', 'payment_status']),
			models.Index(fields=['created_at']),
			models.Index(fields=['user', 'created_at']),
		]
	def __str__(self):
		return f"Order #{self.order_number} - {self.customer_email}"
	def save(self, *args, **kwargs):
		if not self.order_number:
			# Generate unique order number
			date_str = timezone.now().strftime('%Y%m%d')
			random_str = str(uuid.uuid4().int)[:6]
			self.order_number = f"ANIS-{date_str}-{random_str}"
		# Calculate billing if same as shipping
		if self.billing_same_as_shipping:
			self.billing_full_name = self.shipping_full_name
			self.billing_address = self.shipping_address
			self.billing_city = self.shipping_city
			self.billing_state = self.shipping_state
			self.billing_postal_code = self.shipping_postal_code
			self.billing_country = self.shipping_country
		super().save(*args, **kwargs)
	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
	@property
	def customer_name(self):
		return f"{self.customer_first_name} {self.customer_last_name}"
	@property
	def billing_name(self):
		if self.billing_full_name:
			return self.billing_full_name
		return self.customer_name
	@property
	def is_paid(self):
		return self.payment_status == 'paid'
	@property
	def is_completed(self):
		return self.status == 'delivered'
	@property
	def is_cancelled(self):
		return self.status == 'cancelled'
	@property
	def can_cancel(self):
		return self.status in ['pending', 'confirmed', 'processing']
	@property
	def items_count(self):
		return self.items.count()
	@property
	def items_total(self):
		return sum(item.total for item in self.items.all())
	def calculate_totals(self):
		"""Calculate order totals."""
		self.subtotal = self.items_total
		self.total = self.subtotal + self.shipping_fee + self.tax_amount + self.gift_wrapping_fee - self.discount_amount
		self.save()
	def mark_as_paid(self, payment_method, transaction_id=None):
		"""Mark order as paid."""
		self.payment_status = 'paid'
		self.payment_method = payment_method
		self.transaction_id = transaction_id
		self.paid_at = timezone.now()
		# Update status if it was pending
		if self.status == 'pending':
			self.status = 'confirmed'
			self.confirmed_at = timezone.now()
		self.save()
	def mark_as_shipped(self, tracking_number='', carrier='', tracking_url=''):
		"""Mark order as shipped."""
		self.status = 'shipped'
		self.tracking_number = tracking_number
		self.carrier = carrier
		self.tracking_url = tracking_url
		self.shipped_at = timezone.now()
		self.save()
	def mark_as_delivered(self):
		"""Mark order as delivered."""
		self.status = 'delivered'
		self.delivered_at = timezone.now()
		self.save()
	def mark_as_cancelled(self):
		"""Mark order as cancelled."""
		self.status = 'cancelled'
		self.cancelled_at = timezone.now()
		self.payment_status = 'cancelled'
		self.save()
	def get_status_display_with_dates(self):
		"""Get status with dates for display."""
		status_info = {
			'status': self.get_status_display(),
			'created': self.created_at,
			'paid': self.paid_at,
			'confirmed': self.confirmed_at,
			'processing': self.processing_at,
			'shipped': self.shipped_at,
			'delivered': self.delivered_at,
			'cancelled': self.cancelled_at,
		}
		return status_info

class OrderItem(models.Model):
	"""Individual items in an order."""
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	# Product information (snapshot at time of purchase)
	product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True, blank=True)
	variant = models.ForeignKey('store.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
	product_name = models.CharField(max_length=200)
	product_sku = models.CharField(max_length=50, blank=True, default='')
	variant_name = models.CharField(max_length=100, blank=True)
	# Pricing
	unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	total = models.DecimalField(max_digits=10, decimal_places=2)
	# Product details snapshot
	product_image = models.ImageField(upload_to='order_items/', null=True, blank=True)
	concentration = models.CharField(max_length=20, blank=True)
	size_ml = models.IntegerField(null=True, blank=True)
	# Gift options
	is_gift = models.BooleanField(default=False)
	personalization_text = models.CharField(max_length=100, blank=True)
	gift_for = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True, null=True)
	class Meta:
		ordering = ['created_at']
	def __str__(self):
		return f"{self.quantity}x {self.product_name} (Order #{self.order.order_number})"
	def save(self, *args, **kwargs):
		# Calculate total
		if not self.total:
			self.total = self.unit_price * self.quantity
		# Set product details if product exists
		if self.product and not self.product_name:
			self.product_name = self.product.name
			self.product_sku = self.product.sku
			self.concentration = self.product.concentration
			self.size_ml = self.product.size_ml
			if self.product.images.filter(is_primary=True).exists():
				self.product_image = self.product.images.filter(is_primary=True).first().image
		# Set variant details if variant exists
		if self.variant and not self.variant_name:
			self.variant_name = self.variant.variant_name
			self.size_ml = self.variant.size_ml
			self.concentration = self.variant.concentration
		super().save(*args, **kwargs)
	@property
	def full_product_name(self):
		if self.variant_name:
			return f"{self.product_name} - {self.variant_name}"
		return self.product_name

class OrderNote(models.Model):
	"""Internal notes for orders."""
	NOTE_TYPE_CHOICES = (
		('internal', 'Internal Note'),
		('customer', 'Customer Note'),
		('system', 'System Note'),
	)
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notes')
	note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='internal')
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL, 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True
	)
	content = models.TextField()
	is_visible_to_customer = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['-created_at']
	def __str__(self):
		return f"Note for Order #{self.order.order_number}"

class ShippingRate(models.Model):
	"""Shipping rates for different regions and methods."""
	COUNTRY_CHOICES = (
		('NG', 'Nigeria'),
		('GH', 'Ghana'),
		('KE', 'Kenya'),
		('ZA', 'South Africa'),
		('*', 'All Countries'),
	)
	STATE_CHOICES = (
		('LAG', 'Lagos'),
		('ABJ', 'Abuja'),
		('RIV', 'Rivers'),
		('KAN', 'Kano'),
		('*', 'All States'),
	)
	country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='NG')
	state = models.CharField(max_length=10, choices=STATE_CHOICES, default='*')
	shipping_method = models.CharField(max_length=20, choices=Order.SHIPPING_METHOD_CHOICES)
	minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	rate = models.DecimalField(max_digits=10, decimal_places=2)
	free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	is_active = models.BooleanField(default=True)
	estimated_days_min = models.IntegerField(default=3)
	estimated_days_max = models.IntegerField(default=7)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['country', 'state', 'shipping_method']
		unique_together = ['country', 'state', 'shipping_method']
	def __str__(self):
		return f"{self.get_country_display()} - {self.get_state_display()} - {self.get_shipping_method_display()}: ₦{self.rate}"
	def calculate_shipping(self, order_amount):
		"""Calculate shipping cost for order amount."""
		if self.free_shipping_threshold and order_amount >= self.free_shipping_threshold:
			return 0
		return self.rate

class TaxRate(models.Model):
	"""Tax rates for different regions."""
	country = CountryField()
	state = models.CharField(max_length=100, blank=True)
	city = models.CharField(max_length=100, blank=True)
	rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage rate")
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['country', 'state', 'city']
		unique_together = ['country', 'state', 'city']
	def __str__(self):
		location = f"{self.country.name}"
		if self.state:
			location += f", {self.state}"
		if self.city:
			location += f", {self.city}"
		return f"{location}: {self.rate}%"

class Coupon(models.Model):
	"""Discount coupons."""
	COUPON_TYPE_CHOICES = (
		('percentage', 'Percentage'),
		('fixed_amount', 'Fixed Amount'),
		('free_shipping', 'Free Shipping'),
	)
	code = models.CharField(max_length=50, unique=True)
	coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES, default='percentage')
	# Discount values
	discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	# Limits
	minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	# Usage limits
	usage_limit = models.IntegerField(null=True, blank=True, help_text="Maximum number of times this coupon can be used")
	used_count = models.IntegerField(default=0)
	per_user_limit = models.IntegerField(default=1, help_text="Maximum uses per user")
	# Validity
	valid_from = models.DateTimeField()
	valid_to = models.DateTimeField()
	is_active = models.BooleanField(default=True)
	# Applicability
	applicable_to_all_products = models.BooleanField(default=True)
	applicable_categories = models.ManyToManyField('store.Category', blank=True)
	applicable_products = models.ManyToManyField('store.Product', blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['-created_at']
	def __str__(self):
		return f"{self.code} - {self.get_coupon_type_display()}"
	@property
	def is_valid(self):
		"""Check if coupon is currently valid."""
		now = timezone.now()
		return (
			self.is_active and
			self.valid_from <= now <= self.valid_to and
			(self.usage_limit is None or self.used_count < self.usage_limit)
		)
	def calculate_discount(self, order_amount, user=None):
		"""Calculate discount amount for given order."""
		if not self.is_valid:
			return 0
		# Check minimum order amount
		if self.minimum_order_amount and order_amount < self.minimum_order_amount:
			return 0
		# Check user usage limit
		if user and self.per_user_limit:
			from .models import Order
			user_usage = Order.objects.filter(
				user=user,
				coupon=self
			).count()
			if user_usage >= self.per_user_limit:
				return 0
		discount = 0
		if self.coupon_type == 'percentage' and self.discount_percentage:
			discount = (order_amount * self.discount_percentage) / 100
			if self.maximum_discount:
				discount = min(discount, self.maximum_discount)
		elif self.coupon_type == 'fixed_amount' and self.discount_amount:
			discount = min(self.discount_amount, order_amount)
		elif self.coupon_type == 'free_shipping':
			# This is handled separately in shipping calculation
			return 0
		return discount
	def mark_as_used(self):
		"""Increment usage count."""
		self.used_count += 1
		self.save()

class Payment(models.Model):
	"""Payment transaction records."""
	PAYMENT_STATUS_CHOICES = (
		('initiated', 'Initiated'),
		('pending', 'Pending'),
		('successful', 'Successful'),
		('failed', 'Failed'),
		('refunded', 'Refunded'),
	)
	PAYMENT_GATEWAY_CHOICES = (
		('paystack', 'Paystack'),
		('flutterwave', 'Flutterwave'),
		('bank_transfer', 'Bank Transfer'),
		('cash', 'Cash'),
	)
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
	payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAY_CHOICES)
	# Payment details
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	currency = models.CharField(max_length=3, default='NGN')
	status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='initiated')
	# Gateway references
	gateway_reference = models.CharField(max_length=100, blank=True)
	gateway_response = models.JSONField(default=dict, blank=True)
	# Customer payment info (masked)
	card_last4 = models.CharField(max_length=4, blank=True)
	card_brand = models.CharField(max_length=20, blank=True)
	bank_name = models.CharField(max_length=100, blank=True)
	account_number = models.CharField(max_length=20, blank=True)
	# Refund info
	refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	refund_reason = models.TextField(blank=True)
	refunded_at = models.DateTimeField(null=True, blank=True)
	# Metadata
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['-created_at']
	def __str__(self):
		return f"Payment #{self.id} - {self.amount} {self.currency} - {self.get_status_display()}"
	def mark_as_successful(self, gateway_response=None):
		"""Mark payment as successful."""
		self.status = 'successful'
		if gateway_response:
			self.gateway_response = gateway_response
		self.save()
		# Update order payment status
		self.order.mark_as_paid(self.payment_gateway, self.gateway_reference)
	def mark_as_failed(self, gateway_response=None):
		"""Mark payment as failed."""
		self.status = 'failed'
		if gateway_response:
			self.gateway_response = gateway_response
		self.save()
	def refund(self, amount=None, reason=''):
		"""Refund payment."""
		refund_amount = amount or self.amount
		if refund_amount > self.amount - self.refund_amount:
			raise ValueError("Refund amount exceeds available amount")
		self.refund_amount = refund_amount
		self.refund_reason = reason
		self.refunded_at = timezone.now()
		self.status = 'refunded'
		self.save()
		# Update order status if fully refunded
		if self.refund_amount == self.amount:
			self.order.status = 'refunded'
			self.order.save()
	updated_at = models.DateTimeField(auto_now=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	delivered_at = models.DateTimeField(null=True, blank=True)
    
	class Meta:
		ordering = ['-created_at']
