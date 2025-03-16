from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from .utils import verify_email_with_ses
from django.contrib import messages

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_county')
    list_select_related = ('userprofile',)
    actions = ['verify_email_with_ses']
    
    def get_county(self, instance):
        try:
            return instance.userprofile.county
        except UserProfile.DoesNotExist:
            return ''
    
    get_county.short_description = 'County'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

    def verify_email_with_ses(self, request, queryset):
        """Admin action to manually verify a user's email with SES"""
        for user in queryset:
            if user.email:
                success, error_message = verify_email_with_ses(user.email)
                if success:
                    self.message_user(
                        request, 
                        f"Verification email sent to {user.email}", 
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request, 
                        f"Failed to send verification email to {user.email}: {error_message}", 
                        messages.ERROR
                    )
            else:
                self.message_user(
                    request, 
                    f"User {user.username} has no email address", 
                    messages.WARNING
                )
    
    verify_email_with_ses.short_description = "Send SES verification email"

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
