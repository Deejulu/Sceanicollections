from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .forms import UserRegisterForm, UserLoginForm, PasswordResetForm, ProfileUpdateForm, SetNewPasswordForm
from .models import User, PasswordResetToken

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:customer_dashboard')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SceaniCollections, {user.first_name}! Your account has been created successfully.')
            return redirect('dashboard:customer_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create Account - SceaniCollections'})

@csrf_protect
def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        # If already logged in, redirect based on user_type only
        if request.user.user_type in ['admin', 'staff']:
            return redirect('dashboard:admin_dashboard')
        else:
            return redirect('store:product_list')  # Redirect customers to main shop page
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            identifier = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            user = None
            # Check if identifier is an email
            if '@' in identifier:
                try:
                    user_obj = UserModel.objects.get(email__iexact=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except UserModel.DoesNotExist:
                    user = None
            else:
                user = authenticate(request, username=identifier, password=password)
            if user is not None and user.is_active:
                login(request, user)
                # Set session expiry based on remember me
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                # Check user type and redirect accordingly
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                elif user.user_type in ['admin', 'staff']:
                    return redirect('dashboard:admin_dashboard')
                else:
                    return redirect('store:product_list')  # Redirect customers to main shop page
            else:
                messages.error(request, 'Invalid username/email or password. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    context = {
        'form': form,
        'title': 'Login - SceaniCollections',
    }
    return render(request, 'accounts/login.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@csrf_protect
def password_reset_view(request):
    """Handle password reset request - sends email with reset link."""
    # Allow access even if logged in (for testing purposes)
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email__iexact=email)
                
                # Create password reset token
                reset_token = PasswordResetToken.create_token(user)
                
                # Build reset URL
                reset_url = request.build_absolute_uri(f'/accounts/password-reset/confirm/{reset_token.token}/')
                
                # Send email
                try:
                    subject = 'Reset Your Password - SceaniCollections'
                    html_message = render_to_string('accounts/emails/password_reset_email.html', {
                        'user': user,
                        'reset_url': reset_url,
                        'valid_hours': 1,
                    })
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject,
                        plain_message,
                        settings.EMAIL_HOST_USER or 'noreply@sceanicollections.com',
                        [email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.success(request, 'Password reset instructions have been sent to your email. Please check your inbox (and spam folder).')
                except Exception as e:
                    # If email fails, still show success for security (don't reveal if email exists)
                    messages.success(request, 'If an account with that email exists, password reset instructions have been sent.')
                
                return redirect('accounts:password_reset_done')
                
            except User.DoesNotExist:
                # For security, don't reveal if email exists or not
                messages.success(request, 'If an account with that email exists, password reset instructions have been sent.')
                return redirect('accounts:password_reset_done')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {
        'form': form, 
        'title': 'Reset Password - SceaniCollections'
    })


def password_reset_done_view(request):
    """Show confirmation that reset email was sent."""
    return render(request, 'accounts/password_reset_done.html', {
        'title': 'Check Your Email - SceaniCollections'
    })


@csrf_protect
def password_reset_confirm_view(request, token):
    """Handle password reset confirmation with token."""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid:
            messages.error(request, 'This password reset link has expired or already been used. Please request a new one.')
            return redirect('accounts:password_reset')
        
        user = reset_token.user
        
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                # Set new password
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                
                # Mark token as used
                reset_token.mark_as_used()
                
                messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
                return redirect('accounts:password_reset_complete')
        else:
            form = SetNewPasswordForm()
        
        return render(request, 'accounts/password_reset_confirm.html', {
            'form': form,
            'token': token,
            'title': 'Set New Password - SceaniCollections'
        })
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link. Please request a new one.')
        return redirect('accounts:password_reset')


def password_reset_complete_view(request):
    """Show confirmation that password was reset successfully."""
    return render(request, 'accounts/password_reset_complete.html', {
        'title': 'Password Reset Complete - SceaniCollections'
    })

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'accounts/profile.html', {'form': form, 'title': 'My Profile - SceaniCollections', 'user': user})
