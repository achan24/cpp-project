from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'payment_id', 'amount', 'status', 'method', 'created', 'updated']
    list_filter = ['status', 'method', 'created']
    search_fields = ['payment_id', 'order__id', 'order__first_name', 'order__last_name', 'order__email']
    date_hierarchy = 'created'
    raw_id_fields = ['order']
    readonly_fields = ['created', 'updated']
    
    def has_add_permission(self, request):
        # Payments should typically be created through the payment process, not manually
        return False
