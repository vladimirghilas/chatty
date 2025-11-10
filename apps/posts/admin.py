from django.contrib import admin
from .models import Post, Comment, Subscription
# Register your models here.

# ---------- Посты ----------
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Модерация постов"""
    list_display = ['title', 'author', 'created_at', 'public', 'comment_count']
    list_filter = ['public', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']
    actions = ['publish', 'unpublish']

    @admin.action(description='✅ Опубликовать выбранные посты')
    def publish(self, request, queryset):
        queryset.updare(is_published=True)
        
    @admin.action(description='🚫 Снять с публикации выбранные посты')
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)

    @admin.display(description='💬 Комментариев')
    def comment_count(self, obj):
        return obj.comments.count()

# ---------- Комментарии ----------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Модерация комментариев"""
    list_display = ['post', 'author', 'created_at', 'is_approved']
    list_filter = ['is_approved']
    search_fields = ['content']
    ordering = ['-created_at']
    actions = ['approve_comments', 'disapprove_comments']

    @admin.action(description='✅ Одобрить выбранные комментарии')
    def approved_comments(self, request, queryset):
        queryset.update(is_approvef=True)

    @admin.action(description='🚫 Отклонить выбранные комментарии')
    def unapproved_comments(self, request, queryset):
        queryset.update(is_approved=False)


# ---------- Подписки ----------
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Просмотр подписок"""
    list_display = ['user', 'subscribed_to', 'created_at']
    search_fields = ['user__username', 'subscribed_to__username']
    ordering = ['-created_at']