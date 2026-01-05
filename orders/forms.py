from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


class CheckoutForm(forms.Form):
    """Form for checkout process"""
    
    # Contact Information
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': 'your@email.com',
        })
    )
    
    phone = forms.CharField(
        label='Phone Number',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': '+234 XXX XXX XXXX',
        })
    )
    
    # Shipping Information
    full_name = forms.CharField(
        label='Full Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': 'John Doe',
        })
    )
    
    address = forms.CharField(
        label='Street Address',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': '123 Main Street',
        })
    )
    
    city = forms.CharField(
        label='City',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': 'Lagos',
        })
    )
    
    state = forms.CharField(
        label='State/Province',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': 'Lagos State',
        })
    )
    
    postal_code = forms.CharField(
        label='Postal/ZIP Code',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': '100001',
        })
    )
    
    country = CountryField().formfield(
        label='Country',
        initial='NG',
        widget=CountrySelectWidget(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition bg-white',
        })
    )
    
    # Shipping Method
    SHIPPING_CHOICES = [
        ('standard', 'Standard Shipping - ₦2,500 (5-7 business days)'),
        ('express', 'Express Shipping - ₦5,000 (2-3 business days)'),
        ('next_day', 'Next Day Delivery - ₦10,000 (1 business day)'),
        ('pickup', 'Store Pickup - Free (Ready in 24 hours)'),
    ]
    
    shipping_method = forms.ChoiceField(
        label='Shipping Method',
        choices=SHIPPING_CHOICES,
        initial='standard',
        widget=forms.RadioSelect(attrs={
            'class': 'text-amber-500 focus:ring-amber-500',
        })
    )
    
    # Payment Method
    PAYMENT_CHOICES = [
        ('paystack', 'Pay with Paystack'),
        ('flutterwave', 'Pay with Flutterwave'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=PAYMENT_CHOICES,
        initial='paystack',
        widget=forms.RadioSelect(attrs={
            'class': 'text-amber-500 focus:ring-amber-500',
        })
    )
    
    # Additional
    notes = forms.CharField(
        label='Order Notes',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition',
            'placeholder': 'Special instructions for delivery (optional)',
            'rows': 3,
        })
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove any spaces or dashes
        phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
        
        if len(phone) < 10:
            raise forms.ValidationError('Please enter a valid phone number')
        
        return phone
