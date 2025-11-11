from django.core.management.base import BaseCommand
from apps.core.factories import PostFactory, UserFactory, CommentFactory
from random import choice

class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Количество пользователей')
        parser.add_argument('--posts', type=int, default=3, help='Количество постов на пользователя')
        parser.add_argument('--comments', type=int,default=5, help='Количество комментариев на пост')

    def handle(self, *args, **options):
        users_count = options['users']
        posts_per_user = options['posts']
        comments_per_post = options['comments']

        users = UserFactory.create_batch(users_count)
        for user in users:
            posts = PostFactory.create_batch(posts_per_user, author=user)
            for post in posts:
                CommentFactory.create_batch(comments_per_post, post=post, author=choice(users))
        self.stdout.write(self.style.SUCCESS(
            f" Создано {users_count} пользователей, "
            f"{users_count * posts_per_user} постов и "
            f"{users_count * posts_per_user * comments_per_post} комментариев!"
        ))
