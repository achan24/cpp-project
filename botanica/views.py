from django.shortcuts import render, redirect
from django.contrib import messages

def home(request):
    """
    View for the homepage of the Botanica e-commerce platform.
    """
    return render(request, 'home.html')

def about(request):
    """
    View for the About Us page.
    """
    return render(request, 'about.html')

def contact(request):
    """
    View for the Contact Us page.
    Handles contact form submission.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        
        # Here you would typically send an email or save to database
        # For now, we'll just show a success message
        
        messages.success(request, "Thank you for your message! We'll get back to you soon.")
        return redirect('contact')
    
    return render(request, 'contact.html')
