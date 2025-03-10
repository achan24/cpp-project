from django.contrib import admin
from .models import Category, Plant

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'difficulty', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category', 'difficulty']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'name': ('name',)}
    search_fields = ['name', 'description']
    date_hierarchy = 'created'
    ordering = ['name', 'price']
