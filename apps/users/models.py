from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# Функция: сохраняет аватар в отдельной папке для каждого пользователя
def user_avatar_path(instance, filename):
# Пример: avatars/user_3/avatar.png
    return f'avatars/user_{instance.user.id}/{filename}'

# Модель профиля пользователя
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bio = models.TextField("Описание", blank=True, null=True)
    contact = models.CharField("Контактные данные", max_length=255, blank=True, null=True)
    avatar = models.ImageField("Аватар", upload_to=user_avatar_path, blank=True, null=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    @property
    def avatar_url(self):
        """Возвращает ссылку на аватар или дефолтное изображение."""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'  # добавь это изображение в static/images/
