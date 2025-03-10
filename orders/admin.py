from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['plant']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'county', 
                    'status', 'created', 'updated', 'total_price']
    list_filter = ['status', 'created', 'updated', 'county']
    search_fields = ['first_name', 'last_name', 'email', 'address_line1', 'eircode']
    date_hierarchy = 'created'
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'town_or_city', 'county', 'eircode')
        }),
        ('Order Details', {
            'fields': ('status', 'total_price')
        }),
    )
    readonly_fields = ['created', 'updated']
