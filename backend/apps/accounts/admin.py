# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Organization

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'organization', 'role',
        'is_active', 'is_agent', 'date_joined', 'last_login'
    ]
    list_filter = ['role', 'is_active', 'is_agent', 'organization', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('organization', 'role', 'is_agent'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('organization', 'role', 'is_agent'),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing user
            return self.readonly_fields + ('is_agent',)
        return self.readonly_fields

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at', 'user_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    
    def user_count(self, obj):
        count = obj.users.count()
        return format_html(
            '<a href="/admin/accounts/user/?organization__id__exact={}">{}</a>',
            obj.id, count
        )
    user_count.short_description = 'Users'