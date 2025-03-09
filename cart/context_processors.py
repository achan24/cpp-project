from .models import CartItem

def cart(request):
    """
    Context processor to make cart items available to all templates
    """
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart_items = CartItem.objects.filter(session_id=session_id)
    
    total_items = sum(item.quantity for item in cart_items)
    total_price = sum(item.total_price() for item in cart_items)
    
    return {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
    }
