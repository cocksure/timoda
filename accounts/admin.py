from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'phone', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Доп. информация', {'fields': ('phone', 'birth_date', 'avatar')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'country', 'type', 'is_default']
    list_filter = ['type', 'is_default', 'country']
    search_fields = ['user__email', 'full_name', 'city']
