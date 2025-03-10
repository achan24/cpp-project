from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'plant', 'rating', 'short_comment', 'created']
    list_filter = ['rating', 'created', 'plant']
    search_fields = ['user__username', 'plant__name', 'comment']
    date_hierarchy = 'created'
    raw_id_fields = ['user', 'plant']
    readonly_fields = ['created']
    
    def short_comment(self, obj):
        # Return a truncated version of the comment
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    
    short_comment.short_description = 'Comment'
