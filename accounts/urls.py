from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.register, name='register'),
    
    # Login and Logout
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password Management
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change_done/'
    ), name='password_change'),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    # User Profile
    path('profile/', views.profile, name='profile'),
    path('orders/', views.order_history, name='order_history'),
]
