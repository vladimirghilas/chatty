from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Comment, Notification, LikeDislike
from .utils import create_notification

@receiver(post_save, sender=Comment)
def notify_post_author_on_comment(sender, instance, created, **kwargs):
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


# pre_save для LikeDislike
@receiver(pre_save, sender=LikeDislike)
def mark_like_change(sender, instance, **kwargs):
    """
    Отмечаем, является ли лайк новым или изменился ли голос на LIKE.
    """
    if not instance.pk:
        # новый объект
        instance._is_new = True
        instance._changed_to_like = instance.vote == LikeDislike.LIKE
    else:
        # существующий объект
        old_vote = LikeDislike.objects.get(pk=instance.pk).vote
        instance._changed_to_like = old_vote != LikeDislike.LIKE and instance.vote == LikeDislike.LIKE


# post_save для создания уведомления
@receiver(post_save, sender=LikeDislike)
def create_like_notification(sender, instance, created, **kwargs):
    comment = getattr(instance, 'content_object', None)
    if not isinstance(comment, Comment):
        return

    # не уведомляем, если автор комментария совпадает с пользователем, поставившим лайк
    if comment.author == instance.user:
        return

    # уведомляем только при LIKE и только если это первый лайк или голос изменился на LIKE
    if instance.vote == LikeDislike.LIKE and (getattr(instance, '_is_new', False) or getattr(instance, '_changed_to_like', False)):
        author_name = instance.user.username
        Notification.objects.create(
            recipient=comment.author,
            sender=instance.user,
            notification_type='like',
            message=f"{author_name} поставил(а) лайк вашему комментарию",
            comment=comment
        )