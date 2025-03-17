from orders.models import OrderItem

def has_user_purchased_product(user, product_id):
    """
    Check if a user has purchased a specific product.
    Returns True if the user has at least one order containing the product.
    """
    if not user.is_authenticated:
        return False
    
    # Check if the user has any order items with this product
    return OrderItem.objects.filter(
        order__user=user,
        plant_id=product_id
    ).exists()
