from django.contrib import admin
from .models import CartItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_username', 'plant', 'quantity', 'session_id', 'date_added', 'get_total_price']
    list_filter = ['date_added', 'user']
    search_fields = ['user__username', 'plant__name', 'session_id']
    date_hierarchy = 'date_added'
    ordering = ['-date_added']
    
    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    get_username.short_description = 'Username'
    
    def get_total_price(self, obj):
        return obj.total_price()
    get_total_price.short_description = 'Total Price'
