from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """Form for customers to submit feedback."""
    
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'rating', 'subject', 'message', 'customer_name', 'customer_email']
        widgets = {
            'feedback_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm'
            }),
            'rating': forms.RadioSelect(attrs={
                'class': 'rating-input'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm',
                'placeholder': 'Brief subject (optional)'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm resize-none',
                'rows': 4,
                'placeholder': 'Share your experience with us...'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm',
                'placeholder': 'Your name'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm',
                'placeholder': 'Your email'
            }),
        }
    
    def __init__(self, *args, user=None, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.order = order
        
        # Pre-fill user info if authenticated
        if user and user.is_authenticated:
            self.fields['customer_name'].initial = user.get_full_name()
            self.fields['customer_email'].initial = user.email
            self.fields['customer_name'].widget.attrs['readonly'] = True
            self.fields['customer_email'].widget.attrs['readonly'] = True


class QuickFeedbackForm(forms.ModelForm):
    """Simplified feedback form for quick submissions."""
    
    class Meta:
        model = Feedback
        fields = ['rating', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-scent-blue focus:ring-1 focus:ring-scent-blue text-sm resize-none',
                'rows': 3,
                'placeholder': 'Tell us about your experience (optional)...'
            }),
        }
