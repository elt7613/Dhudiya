from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'phone_number', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'phone_number', 'email')
    ordering = ('-date_joined',)
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('username', 'phone_number', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone_number', 'email', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        # Show all users including inactive ones
        return User.objects.all()
