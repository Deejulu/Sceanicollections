from django.db import models
from ckeditor.fields import RichTextField


class SiteSettings(models.Model):
    """Global site settings - only one instance should exist."""
    
    # Site Info
    site_name = models.CharField(max_length=100, default="SceaniCollections")
    site_tagline = models.CharField(max_length=200, default="Luxury Perfumes & Fragrances")
    site_description = models.TextField(blank=True, help_text="Used for SEO meta description")
    
    # Contact Info
    contact_email = models.EmailField(default="info@sceanicollections.com")
    contact_phone = models.CharField(max_length=20, default="+234 XXX XXX XXXX")
    contact_address = models.TextField(blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Business Hours
    business_hours = models.CharField(max_length=100, default="Mon - Sat: 9AM - 6PM")
    
    # Footer
    footer_text = models.TextField(blank=True, default="Your trusted source for authentic luxury perfumes.")
    copyright_text = models.CharField(max_length=200, default="© 2026 SceaniCollections. All rights reserved.")
    
    # SEO
    google_analytics_id = models.CharField(max_length=50, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class HeroSection(models.Model):
    """Hero section content for homepage."""
    
    # Content
    badge_text = models.CharField(max_length=100, default="Premium Collection 2026")
    title_line1 = models.CharField(max_length=100, default="Discover Your")
    title_line2 = models.CharField(max_length=100, default="Signature Scent")
    subtitle = models.TextField(default="Immerse yourself in our curated collection of luxury perfumes, crafted with the world's finest ingredients.")
    
    # CTA Buttons
    cta_primary_text = models.CharField(max_length=50, default="Explore Collection")
    cta_primary_url = models.CharField(max_length=200, default="/shop/")
    cta_secondary_text = models.CharField(max_length=50, default="View Bestsellers")
    cta_secondary_url = models.CharField(max_length=200, default="#featured")
    
    # Image
    hero_image = models.ImageField(upload_to='cms/hero/', blank=True, null=True)
    hero_image_url = models.URLField(blank=True, help_text="External image URL (used if no image uploaded)")
    
    # Stats
    stat1_value = models.CharField(max_length=20, default="500+")
    stat1_label = models.CharField(max_length=50, default="Premium Scents")
    stat2_value = models.CharField(max_length=20, default="50K+")
    stat2_label = models.CharField(max_length=50, default="Happy Customers")
    stat3_value = models.CharField(max_length=20, default="100%")
    stat3_label = models.CharField(max_length=50, default="Authentic")
    
    # Floating Cards
    card1_title = models.CharField(max_length=50, default="Free Delivery")
    card1_subtitle = models.CharField(max_length=50, default="Nationwide")
    card1_icon = models.CharField(max_length=50, default="fa-shipping-fast")
    card2_title = models.CharField(max_length=50, default="100% Original")
    card2_subtitle = models.CharField(max_length=50, default="Guaranteed")
    card2_icon = models.CharField(max_length=50, default="fa-certificate")
    
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"
    
    def __str__(self):
        return f"Hero Section - {self.title_line1}"
    
    def get_image_url(self):
        if self.hero_image:
            return self.hero_image.url
        return self.hero_image_url or "https://images.unsplash.com/photo-1541643600914-78b084683601?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
    
    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()


class HomepageSection(models.Model):
    """Configurable homepage sections."""
    
    SECTION_TYPES = (
        ('featured', 'Featured Products'),
        ('bestsellers', 'Best Sellers'),
        ('new_arrivals', 'New Arrivals'),
        ('categories', 'Shop by Category'),
        ('banner', 'Promotional Banner'),
        ('testimonials', 'Testimonials'),
        ('newsletter', 'Newsletter Signup'),
        ('custom', 'Custom Content'),
    )
    
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    title = models.CharField(max_length=100)
    subtitle = models.TextField(blank=True)
    badge_text = models.CharField(max_length=50, blank=True)
    
    # For banner sections
    banner_image = models.ImageField(upload_to='cms/banners/', blank=True, null=True)
    banner_url = models.CharField(max_length=200, blank=True)
    banner_button_text = models.CharField(max_length=50, blank=True)
    
    # For custom content
    custom_content = RichTextField(blank=True)
    
    # Display settings
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Products to show (for product sections)
    products_to_show = models.IntegerField(default=4)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order']
        verbose_name = "Homepage Section"
        verbose_name_plural = "Homepage Sections"
    
    def __str__(self):
        return f"{self.get_section_type_display()} - {self.title}"


class PromotionalBanner(models.Model):
    """Promotional banners that can be displayed across the site."""
    
    POSITION_CHOICES = (
        ('top', 'Top Banner (Announcement Bar)'),
        ('homepage', 'Homepage Banner'),
        ('shop', 'Shop Page Banner'),
        ('sidebar', 'Sidebar Banner'),
    )
    
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    
    # Content
    text = models.CharField(max_length=200, blank=True)
    subtext = models.CharField(max_length=200, blank=True)
    background_color = models.CharField(max_length=7, default="#D4AF37", help_text="Hex color code")
    text_color = models.CharField(max_length=7, default="#1a1a2e", help_text="Hex color code")
    
    # Image (optional)
    image = models.ImageField(upload_to='cms/banners/', blank=True, null=True)
    
    # Link
    link_url = models.CharField(max_length=200, blank=True)
    link_text = models.CharField(max_length=50, blank=True)
    
    # Display settings
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Promotional Banner"
        verbose_name_plural = "Promotional Banners"
    
    def __str__(self):
        return f"{self.name} ({self.get_position_display()})"
    
    @property
    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class ShopPageContent(models.Model):
    """Content for the shop/products page."""
    
    # Page header
    page_title = models.CharField(max_length=100, default="Our Collection")
    page_subtitle = models.TextField(default="Explore our curated selection of luxury perfumes")
    header_image = models.ImageField(upload_to='cms/shop/', blank=True, null=True)
    
    # Empty state
    empty_title = models.CharField(max_length=100, default="No products found")
    empty_message = models.TextField(default="Check back later for new arrivals.")
    
    # Filter labels
    category_filter_label = models.CharField(max_length=50, default="Categories")
    price_filter_label = models.CharField(max_length=50, default="Price Range")
    sort_label = models.CharField(max_length=50, default="Sort By")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Shop Page Content"
        verbose_name_plural = "Shop Page Content"
    
    def __str__(self):
        return "Shop Page Content"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_content(cls):
        content, created = cls.objects.get_or_create(pk=1)
        return content


class PageContent(models.Model):
    """Generic page content for static pages."""
    
    PAGE_CHOICES = (
        ('about', 'About Us'),
        ('contact', 'Contact Us'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms & Conditions'),
        ('shipping', 'Shipping Policy'),
        ('returns', 'Returns Policy'),
        ('faq', 'FAQ'),
    )
    
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=100)
    content = RichTextField()
    meta_title = models.CharField(max_length=100, blank=True)
    meta_description = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"
    
    def __str__(self):
        return self.get_page_display()


class NewsletterSubscriber(models.Model):
    """Newsletter subscriber model."""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(max_length=64, unique=True, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # Source tracking
    source = models.CharField(max_length=50, default='website', 
        help_text="Where the subscription came from (footer, popup, checkout, etc.)")
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            import secrets
            self.unsubscribe_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def unsubscribe(self):
        from django.utils import timezone
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['is_active', 'unsubscribed_at'])
