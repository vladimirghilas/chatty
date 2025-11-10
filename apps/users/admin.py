from django.contrib import admin
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from ..core.templatetags.my_tags import register

# Register your models here.

admin.site.register(Profile)

# ---------- Пользователи ----------
# Сначала снимаем стандартную регистрацию, чтобы не было конфликта
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Управление пользователями в админке"""
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    actions = ['deactivate_users', 'activate_users']

    @admin.action(description='🔒 Заблокировать выбранных пользователей')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='✅ Разблокировать выбранных пользователей')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
