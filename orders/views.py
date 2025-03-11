from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from products.models import Plant

# Create your views here.
@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your cart is empty. Please add some plants before checking out.")
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            
            # Calculate total price from cart
            total_price = sum(item['price'] * item['quantity'] for item in cart)
            order.total_price = total_price
            order.save()
            
            # Create order items from cart
            for item in cart:
                plant = get_object_or_404(Plant, id=item['plant_id'])
                OrderItem.objects.create(
                    order=order,
                    plant=plant,
                    price=item['price'],
                    quantity=item['quantity']
                )
                
                # Update plant stock
                plant.stock -= item['quantity']
                plant.save()
            
            # Clear the cart
            cart.clear()
            
            # Store order ID in session for payment
            request.session['order_id'] = order.id
            
            # Redirect to payment
            return redirect(reverse('payments:process'))
    else:
        # Pre-fill form with user profile data if available
        initial_data = {}
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'address_line1': profile.address_line1,
                'address_line2': profile.address_line2,
                'town_or_city': profile.town_or_city,
                'county': profile.county,
                'eircode': profile.eircode,
                'phone': profile.phone,
            }
        form = OrderCreateForm(initial=initial_data)
    
    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Ensure users can only view their own orders (unless staff)
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this order.")
        return redirect('accounts:dashboard')
    
    return render(request, 'orders/detail.html', {
        'order': order
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'orders/history.html', {
        'orders': orders
    })
