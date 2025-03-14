from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile

def register(request):
    """
    View for user registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create an empty profile for the user
            UserProfile.objects.create(user=user)
            # Log the user in
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, 'Account created successfully! Please complete your profile.')
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    """
    View for user profile management.
    """
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def order_history(request):
    """
    View for displaying user's order history.
    """
    # This is a placeholder - we'll implement this fully when we create the orders app
    return render(request, 'accounts/order_history.html')
