from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Plant
from .cart import Cart
from .models import CartItem

# Create your views here.

@require_POST
def cart_add(request, product_id):
    """
    Add a product to the cart
    """
    product = get_object_or_404(Plant, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if there's enough stock
    if quantity > product.stock:
        messages.error(request, f"Sorry, we only have {product.stock} of this plant in stock.")
        return redirect(product.get_absolute_url())
    
    cart = Cart(request)
    cart.add(product, quantity=quantity)
    
    messages.success(request, f"{product.name} added to your cart.")
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    """
    Remove a product from the cart
    """
    product = get_object_or_404(Plant, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    
    messages.success(request, f"{product.name} removed from your cart.")
    return redirect('cart:cart_detail')

@require_POST
def cart_update(request, product_id):
    """
    Update the quantity of a product in the cart
    """
    product = get_object_or_404(Plant, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if there's enough stock
    if quantity > product.stock:
        messages.error(request, f"Sorry, we only have {product.stock} of this plant in stock.")
        return redirect('cart:cart_detail')
    
    cart = Cart(request)
    cart.add(product, quantity=quantity, override_quantity=True)
    
    messages.success(request, f"{product.name} quantity updated.")
    return redirect('cart:cart_detail')

def cart_detail(request):
    """
    Display the cart contents
    """
    cart = Cart(request)
    cart_items = list(cart)
    
    # Calculate cart totals
    subtotal = sum(item['total_price'] for item in cart_items)
    
    # Shipping cost calculation (free shipping over €50)
    shipping_cost = 0 if subtotal >= 50 else 5
    total = subtotal + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    
    return render(request, 'cart/cart_detail.html', context)
