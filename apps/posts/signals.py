from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
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