from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTES = (
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike')
    )

    vote = models.SmallIntegerField(choices=VOTES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    public = models.BooleanField(default=True)
    likes = GenericRelation(LikeDislike)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def with_likes_count(cls):
        return cls.objects.annotate(
            likes_count=models.Count('likes', filter=models.Q(likes__vote=LikeDislike.LIKE)),
            dislikes_count=models.Count('likes', filter=models.Q(likes__vote=LikeDislike.DISLIKE))
        )

    def __str__(self):
        return f'{self.title}: {self.author.username}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True)
    likes = GenericRelation(LikeDislike)

    @classmethod
    def with_likes_count(cls):
        return cls.objects.annotate(
            likes_count=models.Count('likes', filter=models.Q(likes__vote=LikeDislike.LIKE)),
            dislikes_count=models.Count('likes', filter=models.Q(likes__vote=LikeDislike.DISLIKE))
        )

    def __repr__(self):
        return f"C: {self.content[:10]} author:{self.author} post: {self.post.title}"


class Notification(models.Model):
    NOTIFICATION_TYPE = (
        ('like', 'New like'),
        ('comment', "New comment")
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='send_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE)
    title = models.CharField(max_length=255, null=True)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True)
    message = models.TextField(null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.notification_type} to {self.recipient.username} from {self.sender.username}'
