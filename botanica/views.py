from django.shortcuts import render

def home(request):
    """
    View for the homepage of the Botanica e-commerce platform.
    """
    return render(request, 'home.html')
