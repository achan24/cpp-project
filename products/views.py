from django.shortcuts import render, get_object_or_404
from .models import Category, Plant

# Create your views here.

def product_list(request, category_id=None):
    """
    View to display a list of plants, optionally filtered by category.
    """
    category = None
    categories = Category.objects.all()
    products = Plant.objects.filter(available=True)
    
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=category)
    
    # Get filter parameters from request
    difficulty = request.GET.get('difficulty')
    sort = request.GET.get('sort')
    
    # Apply difficulty filter if provided
    if difficulty:
        products = products.filter(difficulty=difficulty)
    
    # Apply sorting if provided
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created')
    
    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'selected_difficulty': difficulty,
        'selected_sort': sort,
    }
    
    return render(request, 'products/product_list.html', context)

def product_detail(request, id):
    """
    View to display detailed information about a specific plant.
    """
    product = get_object_or_404(Plant, id=id, available=True)
    
    # Get related products (same category)
    related_products = Plant.objects.filter(category=product.category, available=True).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'products/product_detail.html', context)
