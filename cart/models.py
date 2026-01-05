from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Coupon(models.Model):
	"""Discount coupon model."""
	DISCOUNT_TYPE_CHOICES = [
		('percentage', 'Percentage'),
		('fixed', 'Fixed Amount'),
	]
	
	code = models.CharField(max_length=50, unique=True)
	description = models.TextField(blank=True)
	discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
	discount_value = models.DecimalField(max_digits=10, decimal_places=2)
	
	# Usage limits
	min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
		help_text="Maximum discount for percentage coupons")
	max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
	max_uses_per_user = models.PositiveIntegerField(default=1, help_text="0 = unlimited")
	times_used = models.PositiveIntegerField(default=0)
	
	# Validity
	valid_from = models.DateTimeField(default=timezone.now)
	valid_until = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	
	# Targeting
	first_order_only = models.BooleanField(default=False)
	specific_products = models.ManyToManyField('store.Product', blank=True, related_name='coupons')
	specific_categories = models.ManyToManyField('store.Category', blank=True, related_name='coupons')
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return f"{self.code} ({self.get_discount_display()})"
	
	def get_discount_display(self):
		if self.discount_type == 'percentage':
			return f"{self.discount_value}%"
		return f"₦{self.discount_value}"
	
	def is_valid(self, user=None, cart_total=Decimal('0')):
		"""Check if coupon is valid for use."""
		now = timezone.now()
		
		# Check if active
		if not self.is_active:
			return False, "This coupon is no longer active."
		
		# Check validity period
		if now < self.valid_from:
			return False, "This coupon is not yet valid."
		if self.valid_until and now > self.valid_until:
			return False, "This coupon has expired."
		
		# Check usage limits
		if self.max_uses > 0 and self.times_used >= self.max_uses:
			return False, "This coupon has reached its maximum usage limit."
		
		# Check minimum purchase
		if cart_total < self.min_purchase_amount:
			return False, f"Minimum purchase of ₦{self.min_purchase_amount} required."
		
		# Check user-specific limits
		if user and user.is_authenticated:
			user_uses = CouponUsage.objects.filter(coupon=self, user=user).count()
			if self.max_uses_per_user > 0 and user_uses >= self.max_uses_per_user:
				return False, "You have already used this coupon."
			
			# Check first order only
			if self.first_order_only:
				from orders.models import Order
				if Order.objects.filter(user=user).exists():
					return False, "This coupon is for first-time orders only."
		
		return True, "Coupon is valid."
	
	def calculate_discount(self, cart_items):
		"""Calculate discount amount for cart items."""
		# Get applicable items
		applicable_items = []
		for item in cart_items:
			is_applicable = True
			
			# Check product restrictions
			if self.specific_products.exists():
				if item.product not in self.specific_products.all():
					is_applicable = False
			
			# Check category restrictions
			if self.specific_categories.exists():
				if item.product.category not in self.specific_categories.all():
					is_applicable = False
			
			if is_applicable:
				applicable_items.append(item)
		
		# Calculate applicable subtotal
		applicable_subtotal = sum(item.total_price for item in applicable_items)
		
		if applicable_subtotal == 0:
			return Decimal('0')
		
		# Calculate discount
		if self.discount_type == 'percentage':
			discount = (applicable_subtotal * self.discount_value) / 100
			# Apply max discount cap
			if self.max_discount_amount and discount > self.max_discount_amount:
				discount = self.max_discount_amount
		else:
			discount = min(self.discount_value, applicable_subtotal)
		
		return discount.quantize(Decimal('0.01'))
	
	def use(self, user=None, order=None):
		"""Record coupon usage."""
		self.times_used += 1
		self.save(update_fields=['times_used'])
		
		if user:
			CouponUsage.objects.create(coupon=self, user=user, order=order)


class CouponUsage(models.Model):
	"""Track coupon usage by users."""
	coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
	used_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-used_at']
	
	def __str__(self):
		return f"{self.user.email} used {self.coupon.code}"


class Cart(models.Model):
	"""Shopping cart model."""
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL, 
		on_delete=models.CASCADE, 
		null=True, 
		blank=True, 
		related_name='carts'
	)
	session_key = models.CharField(max_length=40, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Cart status
	is_active = models.BooleanField(default=True)
	is_abandoned = models.BooleanField(default=False)
	abandoned_at = models.DateTimeField(null=True, blank=True)
	# Cart options
	gift_wrapping = models.BooleanField(default=False)
	gift_message = models.TextField(blank=True)
	gift_recipient_name = models.CharField(max_length=100, blank=True)
	gift_recipient_email = models.EmailField(blank=True)
	# Shipping preferences
	shipping_method = models.CharField(max_length=50, blank=True)
	estimated_shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	# Coupon
	coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
	class Meta:
		unique_together = [['user', 'session_key']]
		ordering = ['-created_at']
	def __str__(self):
		if self.user:
			return f"Cart for {self.user.email}"
		return f"Cart (Session: {self.session_key})"
	@property
	def total_items(self):
		"""Return total quantity of items in cart."""
		return sum(item.quantity for item in self.items.all())
	@property
	def subtotal(self):
		"""Calculate subtotal of all items."""
		return sum(item.total_price for item in self.items.all())
	@property
	def discount_amount(self):
		"""Calculate discount from coupon."""
		if self.coupon:
			return self.coupon.calculate_discount(self.items.all())
		return Decimal('0')
	@property
	def total(self):
		"""Calculate total including shipping and discount."""
		return self.subtotal - self.discount_amount + self.estimated_shipping_cost
	def apply_coupon(self, code, user=None):
		"""Apply a coupon to the cart."""
		try:
			coupon = Coupon.objects.get(code__iexact=code)
		except Coupon.DoesNotExist:
			return False, "Invalid coupon code."
		
		is_valid, message = coupon.is_valid(user=user, cart_total=self.subtotal)
		if not is_valid:
			return False, message
		
		self.coupon = coupon
		self.save(update_fields=['coupon'])
		return True, f"Coupon '{coupon.code}' applied! You save ₦{coupon.calculate_discount(self.items.all())}"
	def remove_coupon(self):
		"""Remove coupon from cart."""
		self.coupon = None
		self.save(update_fields=['coupon'])
	def get_or_create_cart_item(self, product, quantity=1):
		"""Get or create a cart item."""
		cart_item, created = CartItem.objects.get_or_create(
			cart=self,
			product=product,
			defaults={'quantity': quantity}
		)
		if not created:
			cart_item.quantity += quantity
			cart_item.save()
		return cart_item
	def update_quantity(self, product_id, quantity):
		"""Update quantity of a specific product."""
		try:
			cart_item = self.items.get(product_id=product_id)
			if quantity <= 0:
				cart_item.delete()
			else:
				cart_item.quantity = quantity
				cart_item.save()
			return True
		except CartItem.DoesNotExist:
			return False
	def remove_item(self, product_id):
		"""Remove an item from cart."""
		try:
			cart_item = self.items.get(product_id=product_id)
			cart_item.delete()
			return True
		except CartItem.DoesNotExist:
			return False
	def clear(self):
		"""Clear all items from cart."""
		self.items.all().delete()
	def mark_as_abandoned(self):
		"""Mark cart as abandoned."""
		self.is_abandoned = True
		self.abandoned_at = timezone.now()
		self.save()
	def to_order(self, order_data):
		"""Convert cart to order."""
		from orders.models import Order, OrderItem
		order = Order.objects.create(
			user=self.user,
			**order_data
		)
		for cart_item in self.items.all():
			OrderItem.objects.create(
				order=order,
				product=cart_item.product,
				product_name=cart_item.product.name,
				price=cart_item.product.price,
				quantity=cart_item.quantity,
				total=cart_item.total_price
			)
		# Update order totals
		order.subtotal = self.subtotal
		order.shipping_fee = self.estimated_shipping_cost
		order.total = self.total
		order.save()
		# Clear the cart
		self.clear()
		self.is_active = False
		self.save()
		return order

class CartItem(models.Model):
	"""Individual item in shopping cart."""
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	added_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# For variants
	variant = models.ForeignKey(
		'store.ProductVariant', 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True
	)
	# Customization options
	personalization_text = models.CharField(max_length=100, blank=True)
	gift_for = models.CharField(max_length=100, blank=True)
	is_gift = models.BooleanField(default=False)
	class Meta:
		ordering = ['-added_at']
		unique_together = [['cart', 'product', 'variant']]
	def __str__(self):
		variant_info = f" ({self.variant.variant_name})" if self.variant else ""
		return f"{self.quantity}x {self.product.name}{variant_info}"
	@property
	def unit_price(self):
		"""Get unit price based on variant or product."""
		if self.variant:
			return self.variant.price
		return self.product.price
	@property
	def total_price(self):
		"""Calculate total price for this item."""
		return self.unit_price * self.quantity
	@property
	def product_name(self):
		"""Get product name with variant if applicable."""
		if self.variant:
			return f"{self.product.name} - {self.variant.variant_name}"
		return self.product.name
	def increase_quantity(self, amount=1):
		"""Increase quantity by specified amount."""
		self.quantity += amount
		self.save()
	def decrease_quantity(self, amount=1):
		"""Decrease quantity by specified amount."""
		if self.quantity > amount:
			self.quantity -= amount
			self.save()
		else:
			self.delete()
