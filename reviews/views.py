from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from products.models import Plant
from .models import Review
from .forms import ReviewForm
from .utils import has_user_purchased_product

# Create your views here.

@login_required
def add_review(request, product_id):
    """
    View for adding a new review for a product.
    Only allows users who have purchased the product to leave a review.
    """
    product = get_object_or_404(Plant, id=product_id, available=True)
    
    # Check if user has purchased this product
    if not has_user_purchased_product(request.user, product_id):
        messages.warning(
            request, 
            "You can only review products you've purchased. Browse your order history to find products to review."
        )
        return redirect('products:product_detail', id=product_id)
    
    # Check if user has already reviewed this product
    existing_review = Review.objects.filter(user=request.user, plant=product).first()
    if existing_review:
        return redirect('reviews:edit_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.plant = product
            review.save()
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('products:product_detail', id=product_id)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'product': product,
        'action': 'Add'
    })

@login_required
def edit_review(request, review_id):
    """
    View for editing an existing review.
    Users can only edit their own reviews.
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.plant
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('products:product_detail', id=product.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'product': product,
        'review': review,
        'action': 'Edit'
    })
