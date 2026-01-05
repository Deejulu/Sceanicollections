from django.db import models
from django.conf import settings
from orders.models import Order


class Feedback(models.Model):
    """Customer feedback model - captures feedback during/after order process."""
    
    RATING_CHOICES = (
        (5, 'Excellent'),
        (4, 'Very Good'),
        (3, 'Good'),
        (2, 'Fair'),
        (1, 'Poor'),
    )
    
    FEEDBACK_TYPE_CHOICES = (
        ('checkout_experience', 'Checkout Experience'),
        ('website_usability', 'Website Usability'),
        ('product_selection', 'Product Selection'),
        ('payment_process', 'Payment Process'),
        ('general', 'General Feedback'),
        ('suggestion', 'Suggestion'),
        ('complaint', 'Complaint'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
        ('resolved', 'Resolved'),
    )
    
    # Link to user and order (optional)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks'
    )
    
    # Feedback details
    feedback_type = models.CharField(
        max_length=30,
        choices=FEEDBACK_TYPE_CHOICES,
        default='general'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
        help_text="Overall rating from 1 to 5"
    )
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(help_text="Customer feedback message")
    
    # Contact info (for guests)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Admin tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin"
    )
    admin_response = models.TextField(
        blank=True,
        help_text="Response sent to customer"
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responded_feedbacks'
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Customer Feedback'
        verbose_name_plural = 'Customer Feedbacks'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"Feedback from {self.user.email} - {self.get_feedback_type_display()}"
        elif self.customer_email:
            return f"Feedback from {self.customer_email} - {self.get_feedback_type_display()}"
        return f"Anonymous Feedback - {self.get_feedback_type_display()}"
    
    @property
    def is_new(self):
        return self.status == 'new'
    
    @property
    def rating_stars(self):
        """Return HTML stars for rating display."""
        if not self.rating:
            return "No rating"
        return "★" * self.rating + "☆" * (5 - self.rating)
