from decimal import Decimal
from django.conf import settings
from products.models import Plant
from .models import CartItem

class Cart:
    """
    A class to handle cart operations
    """
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user
        
    def __iter__(self):
        """
        Iterate over the items in the cart and get the plants from the database
        """
        if self.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=self.user)
        else:
            session_id = self.session.session_key
            if not session_id:
                self.session.create()
                session_id = self.session.session_key
            cart_items = CartItem.objects.filter(session_id=session_id)
        
        for item in cart_items:
            yield {
                'plant_id': item.plant.id,
                'name': item.plant.name,
                'price': Decimal(str(item.plant.price)),
                'quantity': item.quantity,
                'total_price': item.plant.price * item.quantity,
                'image': item.plant.image.url if item.plant.image else None,
            }
    
    def __len__(self):
        """
        Count all items in the cart
        """
        if self.user.is_authenticated:
            return CartItem.objects.filter(user=self.user).count()
        else:
            session_id = self.session.session_key
            if not session_id:
                return 0
            return CartItem.objects.filter(session_id=session_id).count()
    
    def add(self, plant, quantity=1, override_quantity=False):
        """
        Add a plant to the cart or update its quantity
        """
        plant_obj = Plant.objects.get(id=plant.id)
        
        if self.user.is_authenticated:
            cart_item, created = CartItem.objects.get_or_create(
                user=self.user,
                plant=plant_obj,
                defaults={'quantity': 0}
            )
        else:
            session_id = self.session.session_key
            if not session_id:
                self.session.create()
                session_id = self.session.session_key
            
            cart_item, created = CartItem.objects.get_or_create(
                session_id=session_id,
                plant=plant_obj,
                defaults={'quantity': 0}
            )
        
        if override_quantity:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        
        cart_item.save()
    
    def remove(self, plant):
        """
        Remove a plant from the cart
        """
        if self.user.is_authenticated:
            CartItem.objects.filter(user=self.user, plant=plant).delete()
        else:
            session_id = self.session.session_key
            if session_id:
                CartItem.objects.filter(session_id=session_id, plant=plant).delete()
    
    def clear(self):
        """
        Remove all items from the cart
        """
        if self.user.is_authenticated:
            CartItem.objects.filter(user=self.user).delete()
        else:
            session_id = self.session.session_key
            if session_id:
                CartItem.objects.filter(session_id=session_id).delete()
