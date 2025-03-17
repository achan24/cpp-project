from django.shortcuts import render, get_object_or_404
from .models import Category, Plant
from django.db import models

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
    
    # Get reviews for this product
    reviews = product.reviews.all()
    
    # Check if the current user has purchased this product
    user_has_purchased = False
    user_review = None
    
    if request.user.is_authenticated:
        from reviews.utils import has_user_purchased_product
        user_has_purchased = has_user_purchased_product(request.user, id)
        user_review = product.reviews.filter(user=request.user).first()
    
    # Calculate average rating
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    # Count reviews by rating
    rating_counts = {
        '5': reviews.filter(rating=5).count(),
        '4': reviews.filter(rating=4).count(),
        '3': reviews.filter(rating=3).count(),
        '2': reviews.filter(rating=2).count(),
        '1': reviews.filter(rating=1).count(),
    }
    
    # Calculate percentages for the rating bars
    total_reviews = reviews.count()
    if total_reviews > 0:
        for rating in rating_counts:
            rating_counts[rating] = {
                'count': rating_counts[rating],
                'percentage': (rating_counts[rating] / total_reviews) * 100
            }
    
    # Apply rating filter if provided
    selected_rating = request.GET.get('rating')
    if selected_rating:
        reviews = reviews.filter(rating=selected_rating)
    
    # Apply sorting if provided
    selected_sort = request.GET.get('sort', 'newest')
    if selected_sort == 'oldest':
        reviews = reviews.order_by('created')
    else:  # Default to newest
        reviews = reviews.order_by('-created')
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rating_counts': rating_counts,
        'total_reviews': total_reviews,
        'user_has_purchased': user_has_purchased,
        'user_review': user_review,
        'selected_rating': selected_rating,
        'selected_sort': selected_sort,
    }
    
    return render(request, 'products/product_detail.html', context)
