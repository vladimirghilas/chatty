import factory
from django.contrib.auth.models import User
from apps.posts.models import Post, Comment
from faker import Faker

faker_ru = Faker('ru_RU')


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User  # Указываем, какую модель будет создавать эта фабрика
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user_{n}')  # Генерирует user_0, user_1 и т.д.
    email = factory.Sequence(lambda o: f'user_{o}@example.com')
    password = factory.PostGenerationMethodCall('set_password', '1234')

    @factory.post_generation
    def save_password_changes(self, create, extracted, **kwargs):
        if create:
            self.save()


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.LazyAttribute(lambda obj: faker_ru.sentence())
    content = factory.LazyAttribute(lambda obj: " ".join(faker_ru.paragraphs(nb=3)))
    views_count = factory.Faker('random_int', min=0, max=1000)
    public = factory.Faker('boolean')
    author = factory.SubFactory(UserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    content = factory.LazyAttribute(lambda obj: " ".join(faker_ru.paragraphs(nb=3)))
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)
