from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

class UserManager(BaseUserManager):
    """Manager for default username-based User model."""
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, email, password, **extra_fields)

class User(AbstractUser):
	"""Default Django User model with username required and email optional."""
	USER_TYPE_CHOICES = (
		('customer', 'Customer'),
		('admin', 'Admin'),
		('staff', 'Staff'),
	)
	# username field is inherited from AbstractUser, but we set a default for migration safety
	username = models.CharField(
		max_length=150,
		unique=True,
		default='user_default',
		help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
		validators=[AbstractUser.username_validator],
		error_messages={
			'unique': "A user with that username already exists.",
		},
	)
	email = models.EmailField(_('email address'), blank=True, null=True)
	user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
	# Personal Information
	phone = models.CharField(max_length=20, blank=True)
	profile_image = models.ImageField(upload_to='users/profile_images/', blank=True, null=True)
	date_of_birth = models.DateField(null=True, blank=True)
	# Verification
	email_verified = models.BooleanField(default=False)
	# Preferences
	newsletter_subscribed = models.BooleanField(default=True)
	objects = UserManager()

	class Meta:
		ordering = ['-date_joined']
		verbose_name = _('user')
		verbose_name_plural = _('users')

	def __str__(self):
		return self.email

	@property
	def full_name(self):
		return f"{self.first_name} {self.last_name}".strip()

	@property
	def is_admin_user(self):
		"""Check if user is admin or staff by user_type only."""
		return self.user_type in ['admin', 'staff']

	@property
	def is_customer_user(self):
		"""Check if user is a customer by user_type only."""
		return self.user_type == 'customer'

class Address(models.Model):
	"""Shipping/Billing address for users."""
	ADDRESS_TYPE_CHOICES = (
		('shipping', 'Shipping'),
		('billing', 'Billing'),
		('both', 'Both'),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
	address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='shipping')
	is_default = models.BooleanField(default=False)
	# Address details
	full_name = models.CharField(max_length=100)
	phone = PhoneNumberField()
	street_address = models.CharField(max_length=255)
	apartment = models.CharField(max_length=100, blank=True)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	postal_code = models.CharField(max_length=20)
	country = CountryField()
	# Additional info
	delivery_instructions = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'accounts'
		verbose_name_plural = "Addresses"
		ordering = ['-is_default', '-created_at']
	def __str__(self):
		return f"{self.full_name} - {self.city}, {self.country}"
	def get_full_address(self):
		"""Return formatted full address."""
		parts = [
			self.street_address,
			self.apartment,
			f"{self.city}, {self.state} {self.postal_code}",
			str(self.country.name)
		]
		return ", ".join(filter(None, parts))

class Wishlist(models.Model):
	"""User's wishlist of products."""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
	products = models.ManyToManyField('store.Product', related_name='wishlisted_by', blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		app_label = 'accounts'
	def __str__(self):
		return f"{self.user.email}'s Wishlist"
	def add_product(self, product):
		"""Add a product to wishlist."""
		self.products.add(product)
	def remove_product(self, product):
		"""Remove a product from wishlist."""
		self.products.remove(product)
	def contains(self, product):
		"""Check if product is in wishlist."""
		return self.products.filter(id=product.id).exists()
	@property
	def count(self):
		return self.products.count()


class PasswordResetToken(models.Model):
	"""Token for password reset functionality."""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
	token = models.CharField(max_length=100, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField()
	used = models.BooleanField(default=False)
	used_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		app_label = 'accounts'
		ordering = ['-created_at']

	def __str__(self):
		return f"Password reset token for {self.user.email}"

	@property
	def is_expired(self):
		from django.utils import timezone
		return timezone.now() > self.expires_at

	@property
	def is_valid(self):
		return not self.used and not self.is_expired

	@classmethod
	def create_token(cls, user):
		"""Create a new password reset token for a user."""
		import secrets
		from django.utils import timezone
		from datetime import timedelta
		
		# Invalidate any existing unused tokens
		cls.objects.filter(user=user, used=False).update(used=True)
		
		# Create new token (valid for 1 hour)
		token = secrets.token_urlsafe(32)
		expires_at = timezone.now() + timedelta(hours=1)
		
		return cls.objects.create(
			user=user,
			token=token,
			expires_at=expires_at
		)

	def mark_as_used(self):
		"""Mark token as used."""
		from django.utils import timezone
		self.used = True
		self.used_at = timezone.now()
		self.save()

