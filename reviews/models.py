from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from store.models import Product


class Review(models.Model):
    """Product review model."""
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Review aspects specific to perfumes
    longevity_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How long does the scent last?"
    )
    sillage_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How strong is the projection?"
    )
    value_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Value for money"
    )
    
    # Helpful votes
    helpful_count = models.PositiveIntegerField(default=0)
    
    # Verification
    verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)  # For moderation
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per product per user
        
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.product.name} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        # Check if user has purchased this product
        from orders.models import Order, OrderItem
        has_purchased = OrderItem.objects.filter(
            order__user=self.user,
            product=self.product,
            order__status='delivered'
        ).exists()
        self.verified_purchase = has_purchased
        super().save(*args, **kwargs)
        
        # Update product average rating
        self.product.update_rating()


class ReviewHelpful(models.Model):
    """Track which users found a review helpful."""
    
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='helpful_votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
        
    def __str__(self):
        return f"{self.user.email} found review #{self.review.id} helpful"
