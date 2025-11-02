from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Comment, Post, Notification, LikeDislike
from .utils import create_notification


@receiver(post_save, sender=Comment)
def notify_post_author_on_comment(sender, instance, created, **kwargs):
    """Уведомление автора поста о новом комментарии."""
    message = f"{instance.author.username} оставил комментарий к вашему посту: {instance.post.title}"
    if created and instance.post.author != instance.author:
        create_notification(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type='comment',
            message=message,
            post=instance.post,
            comment=instance
        )


# --- pre_save для LikeDislike ---
@receiver(pre_save, sender=LikeDislike)
def mark_like_change(sender, instance, **kwargs):
    """Отмечаем, является ли лайк новым или изменился ли голос на LIKE."""
    if not instance.pk:
        instance._is_new = True
        instance._changed_to_like = instance.vote == LikeDislike.LIKE
    else:
        old_vote = LikeDislike.objects.get(pk=instance.pk).vote
        instance._changed_to_like = old_vote != LikeDislike.LIKE and instance.vote == LikeDislike.LIKE


# --- post_save для LikeDislike (комментарии + посты) ---
@receiver(post_save, sender=LikeDislike)
def create_like_notification(sender, instance, created, **kwargs):
    """Создание уведомлений о лайках (для постов и комментариев)."""
    obj = instance.content_object

    # только для лайков
    if instance.vote != LikeDislike.LIKE:
        return

    # только если лайк новый или изменился с дизлайка на лайк
    if not (getattr(instance, '_is_new', False) or getattr(instance, '_changed_to_like', False)):
        return

    # --- если лайк поставлен комментарию ---
    if isinstance(obj, Comment):
        if obj.author != instance.user:
            Notification.objects.create(
                recipient=obj.author,
                sender=instance.user,
                notification_type='like',
                message=f"{instance.user.username} поставил(а) лайк вашему комментарию",
                comment=obj
            )

    # --- если лайк поставлен посту ---
    elif isinstance(obj, Post):
        if obj.author != instance.user:
            Notification.objects.create(
                recipient=obj.author,
                sender=instance.user,
                notification_type='like',
                message=f"{instance.user.username} поставил(а) лайк вашему посту: {obj.title}",
                post=obj
            )