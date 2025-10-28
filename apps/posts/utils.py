from .models import Notification

def create_notification(recipient, sender, notification_type, message, post=None, comment=None):
    if recipient == sender:
        return None
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        message=message,
        post=post,
        comment=comment
    )