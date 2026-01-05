from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from ckeditor.fields import RichTextField
import uuid

# ...existing code...

# PaymentMethod model definition (moved below imports)
class PaymentMethod(models.Model):
    """Payment method model for admin control."""
    name = models.CharField(max_length=50, unique=True)
    code = models.SlugField(max_length=50, unique=True, help_text="Short code for use in code, e.g. 'paystack', 'bank_transfer'")
    is_active = models.BooleanField(default=True, help_text="Should this payment method be available to customers?")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which to display payment methods.")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'

    def __str__(self):
        return self.name
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from ckeditor.fields import RichTextField
import uuid

class Category(models.Model):
	"""Product category model."""
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	description = models.TextField(blank=True)
	image = models.ImageField(upload_to='categories/', blank=True, null=True)
	parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
	is_active = models.BooleanField(default=True)
	featured = models.BooleanField(default=False)
	meta_title = models.CharField(max_length=100, blank=True)
	meta_description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		verbose_name_plural = "Categories"
		ordering = ['name']
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	def get_absolute_url(self):
		return reverse('store:category_detail', kwargs={'slug': self.slug})
	@property
	def has_children(self):
		return self.children.exists()

class Brand(models.Model):
	"""Perfume brand model."""
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	description = RichTextField(blank=True)
	logo = models.ImageField(upload_to='brands/logo/', blank=True, null=True)
	banner = models.ImageField(upload_to='brands/banners/', blank=True, null=True)
	established_year = models.IntegerField(null=True, blank=True)
	country_of_origin = models.CharField(max_length=100, blank=True)
	website = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		ordering = ['name']
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	def get_absolute_url(self):
		return reverse('store:brand_detail', kwargs={'slug': self.slug})

class ScentNote(models.Model):
	"""Scent note model (top, heart, base notes)."""
	NOTE_TYPE_CHOICES = (
		('top', 'Top Note'),
		('heart', 'Heart/Middle Note'),
		('base', 'Base Note'),
	)
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	note_type = models.CharField(max_length=10, choices=NOTE_TYPE_CHOICES)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
	color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		ordering = ['note_type', 'name']
	def __str__(self):
		return f"{self.get_note_type_display()}: {self.name}"
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

class Product(models.Model):
	"""Main product model for perfumes."""
	CONCENTRATION_CHOICES = (
		('parfum', 'Parfum (Extrait)'),
		('edp', 'Eau de Parfum (EDP)'),
		('edt', 'Eau de Toilette (EDT)'),
		('cologne', 'Eau de Cologne'),
		('oil', 'Perfume Oil'),
		('attar', 'Attar'),
	)
	GENDER_CHOICES = (
		('men', 'For Him'),
		('women', 'For Her'),
		('unisex', 'Unisex'),
	)
	SEASON_CHOICES = (
		('spring', 'Spring'),
		('summer', 'Summer'),
		('fall', 'Fall/Autumn'),
		('winter', 'Winter'),
		('all_season', 'All Season'),
	)
	# Basic Information
	sku = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True, blank=True)
	brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
	# Product Details
	concentration = models.CharField(max_length=20, choices=CONCENTRATION_CHOICES)
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
	size_ml = models.IntegerField(help_text="Size in milliliters")
	# Descriptions
	short_description = models.TextField()
	full_description = RichTextField()
	ingredients = RichTextField(blank=True)
	how_to_use = RichTextField(blank=True)
	# Pricing
	price = models.DecimalField(max_digits=10, decimal_places=2)
	compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	# Inventory
	stock_quantity = models.IntegerField(default=0)
	low_stock_threshold = models.IntegerField(default=5)
	allow_backorder = models.BooleanField(default=False)
	is_available = models.BooleanField(default=True)
	# Scent Information
	scent_notes = models.ManyToManyField(ScentNote, through='ProductScentNote', related_name='products')
	top_notes = models.CharField(max_length=500, blank=True, help_text="Comma separated")
	heart_notes = models.CharField(max_length=500, blank=True, help_text="Comma separated")
	base_notes = models.CharField(max_length=500, blank=True, help_text="Comma separated")
	# Performance
	longevity = models.CharField(max_length=50, blank=True, help_text="e.g., 8-10 hours")
	sillage = models.CharField(max_length=50, blank=True, help_text="e.g., Moderate, Strong")
	season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all_season')
	occasion = models.CharField(max_length=200, blank=True, help_text="e.g., Day, Night, Formal, Casual")
	# Flags
	is_featured = models.BooleanField(default=False)
	is_bestseller = models.BooleanField(default=False)
	is_new = models.BooleanField(default=True)
	is_sale = models.BooleanField(default=False)
	is_limited_edition = models.BooleanField(default=False)
	# SEO
	meta_title = models.CharField(max_length=100, blank=True)
	meta_description = models.TextField(blank=True)
	meta_keywords = models.CharField(max_length=200, blank=True)
	# Analytics
	view_count = models.IntegerField(default=0)
	purchase_count = models.IntegerField(default=0)
	# Ratings (updated by reviews)
	average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
	review_count = models.IntegerField(default=0)
	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	release_date = models.DateField(null=True, blank=True)
	class Meta:
		app_label = 'store'
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['slug', 'is_available']),
			models.Index(fields=['price', 'is_available']),
			models.Index(fields=['is_featured', 'is_available']),
			models.Index(fields=['is_bestseller', 'is_available']),
		]
	def __str__(self):
		return f"{self.name} ({self.brand.name if self.brand else 'No Brand'})"
	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.name)
			slug = base_slug
			counter = 1
			while Product.objects.filter(slug=slug).exists():
				slug = f"{base_slug}-{counter}"
				counter += 1
			self.slug = slug
		super().save(*args, **kwargs)
	def get_absolute_url(self):
		return reverse('store:product_detail', kwargs={'slug': self.slug})
	@property
	def discount_percentage(self):
		if self.compare_price and self.compare_price > self.price:
			discount = ((self.compare_price - self.price) / self.compare_price) * 100
			return round(discount, 0)
		return 0
	@property
	def in_stock(self):
		return self.stock_quantity > 0
	@property
	def low_stock(self):
		return 0 < self.stock_quantity <= self.low_stock_threshold
	@property
	def out_of_stock(self):
		return self.stock_quantity <= 0
	def increment_view_count(self):
		self.view_count += 1
		self.save(update_fields=['view_count'])
	def increment_purchase_count(self):
		self.purchase_count += 1
		self.save(update_fields=['purchase_count'])
	
	def update_rating(self):
		"""Update average rating from reviews."""
		from django.db.models import Avg, Count
		stats = self.reviews.filter(is_approved=True).aggregate(
			avg_rating=Avg('rating'),
			count=Count('id')
		)
		self.average_rating = stats['avg_rating'] or 0
		self.review_count = stats['count'] or 0
		self.save(update_fields=['average_rating', 'review_count'])

class ProductScentNote(models.Model):
	"""Intermediate model for product scent notes with intensity."""
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	scent_note = models.ForeignKey(ScentNote, on_delete=models.CASCADE)
	intensity = models.IntegerField(default=5, choices=[(i, str(i)) for i in range(1, 11)])
	class Meta:
		app_label = 'store'
		unique_together = ['product', 'scent_note']
		ordering = ['scent_note__note_type', '-intensity']
	def __str__(self):
		return f"{self.product.name} - {self.scent_note.name} ({self.intensity}/10)"

class ProductImage(models.Model):
	"""Product images model."""
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
	image = models.ImageField(upload_to='products/images/')
	alt_text = models.CharField(max_length=200, blank=True)
	is_primary = models.BooleanField(default=False)
	order = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	class Meta:
		app_label = 'store'
		ordering = ['is_primary', 'order', 'created_at']
	def __str__(self):
		return f"{self.product.name} - Image {self.id}"
	def save(self, *args, **kwargs):
		# If this is set as primary, unset any other primary images for this product
		if self.is_primary:
			ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
		super().save(*args, **kwargs)

class ProductVariant(models.Model):
	"""Product variants (different sizes, concentrations)."""
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
	size_ml = models.IntegerField()
	concentration = models.CharField(max_length=20, choices=Product.CONCENTRATION_CHOICES)
	sku = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	stock_quantity = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		unique_together = ['product', 'size_ml', 'concentration']
		ordering = ['size_ml']
	def __str__(self):
		return f"{self.product.name} - {self.size_ml}ml {self.get_concentration_display()}"
	@property
	def in_stock(self):
		return self.stock_quantity > 0
	@property
	def variant_name(self):
		return f"{self.size_ml}ml {self.get_concentration_display()}"

class Collection(models.Model):
	"""Product collections."""
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	description = RichTextField(blank=True)
	image = models.ImageField(upload_to='collections/', blank=True, null=True)
	products = models.ManyToManyField(Product, related_name='collections', blank=True)
	featured = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		ordering = ['-featured', 'name']
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	def get_absolute_url(self):
		return reverse('store:collection_detail', kwargs={'slug': self.slug})

class SampleSet(models.Model):
	"""Perfume sample sets."""
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True, blank=True)
	description = RichTextField(blank=True)
	products = models.ManyToManyField(Product, through='SampleSetProduct', related_name='sample_sets')
	price = models.DecimalField(max_digits=10, decimal_places=2)
	compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	sample_size_ml = models.IntegerField(default=2, help_text="Size of each sample in ml")
	number_of_samples = models.IntegerField(default=5)
	is_customizable = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'store'
		ordering = ['-created_at']
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	@property
	def discount_percentage(self):
		if self.compare_price and self.compare_price > self.price:
			discount = ((self.compare_price - self.price) / self.compare_price) * 100
			return round(discount, 0)
		return 0

class SampleSetProduct(models.Model):
	"""Products included in a sample set."""
	sample_set = models.ForeignKey(SampleSet, on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	order = models.IntegerField(default=0)
	class Meta:
		app_label = 'store'
		ordering = ['order']
		unique_together = ['sample_set', 'product']
	def __str__(self):
		return f"{self.sample_set.name} - {self.product.name}"
    
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
    
	class Meta:
		ordering = ['-created_at']
    
	def __str__(self):
		return self.name



# Import CMS models to make them available from store.models
from .cms_models import (
	SiteSettings,
	HeroSection,
	HomepageSection,
	PromotionalBanner,
	ShopPageContent,
	PageContent,
)