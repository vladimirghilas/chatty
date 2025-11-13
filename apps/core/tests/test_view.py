from http.client import responses
from django.contrib.auth.models import User, AnonymousUser
from django.test import Client, RequestFactory
from apps.core.factories import UserFactory, PostFactory
from django.urls import reverse
from apps.posts.models import Comment, Post
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from apps.posts.views import create_post

import pytest


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента"""
    return Client()


@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    """Фикстура для создания аутентифицированного клиента"""
    client.force_login(user)
    return client, user


@pytest.fixture
def post(user):
    """Фикстура для создания post"""
    return PostFactory(author=user)


@pytest.fixture
def comment_data(post):
    """Фикстура для данных комментария"""
    return {
        'content': 'Тестовый комментарий',
        'post_id': post.id
    }


@pytest.mark.django_db
class TestCommentAdd:
    """Тесты для функции comment_add"""

    def test_comment_add_success(self, authenticated_client, post, comment_data):
        """Тест успешного добавления комментария"""
        client, user = authenticated_client
        # Проверяем, что пользователь аутентифицирован
        assert user.is_authenticated

        # Отправляем POST запрос для добавления комментария
        response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)

        # Проверяем, что произошло перенаправление на страницу post_detail
        assert response.status_code == 302
        assert response.url == reverse('posts:post_detail', kwargs={'post_id': post.id})

        # Проверяем, что комментарий был создан в базе данных
        comment = Comment.objects.filter(post=post).first()
        assert comment is not None
        assert comment.content == comment_data['content']
        assert comment.author == user
        assert comment.post == post

    def test_comment_add_not_authenticated(self, client, post, comment_data):
        """Тест попытки добавления комментария неаутентифицированным пользователем"""
        response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)
        # Проверяем, что произошло перенаправление на страницу входа

        assert response.status_code == 302
        assert '/login' in response.url

        # Проверяем, что комментарий не был создан
        comment_count = Comment.objects.filter(post=post).count()
        assert comment_count == 0

    def test_comment_add_invalid_post_id(self, client, authenticated_client, comment_data):
        """Тест добавления комментария к несуществующему post"""
        client, user = authenticated_client

        # Устанавливаем несуществующий ID post
        comment_data['post.id'] = 9999
        # Отправляем POST запрос
        response = client.post(reverse('posts:add_comment', args=[9999]), comment_data)
        # Проверяем, что получили 404 ошибку
        assert response.status_code == 404
        # Проверяем, что комментарий не был создан
        comment_count = Comment.objects.count()
        assert comment_count == 0

    def test_comment_add_invalid_form_data(self, authenticated_client, post):
        # Проверяем, что комментарий не был создан
        client, user = authenticated_client
        # Отправляем пустой текст комментария
        comment_data = {
            'content': '',
            'post_id': post.id
        }
        # Отправляем POST запрос
        response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)
        # Проверяем, что произошло перенаправление (форма невалидна, но post существует)
        assert response.status_code == 302
        assert response.url == reverse('posts:post_detail', kwargs={'post_id': post.id})
        # Проверяем, что комментарий не был создан из-за невалидности формы
        comment_count = Comment.objects.filter(post=post).count()
        assert comment_count == 0

    def test_comment_add_get_request(self, authenticated_client, post):
        """Тест GET запроса к comment_add (должен вернуть 302)"""
        client, user = authenticated_client
        response = client.get(reverse('posts:add_comment', args=[post.id]))
        # Проверяем, что получили 302 ошибку
        assert response.status_code == 302

    def test_comment_add_multiple_comments(self, authenticated_client, post):
        """Тест добавления нескольких комментариев к одному post"""
        client, user = authenticated_client
        comment_data = [
            {'content': 'Первый комментарий', 'post_id': post.id},
            {'content': 'Второй комментарий', 'post_id': post.id},
            {'content': 'Третий комментарий', 'post_id': post.id}
        ]
        # Добавляем несколько комментариев
        for comment_data in comment_data:
            response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)
            assert response.status_code == 302

        # Проверяем, что все комментарии были созданы
        comments = Comment.objects.filter(post=post)
        assert comments.count() == 3

        # Проверяем содержимое комментариев
        comment_texts = [comment.content for comment in comments]
        expected_texts = ['Первый комментарий', 'Второй комментарий', 'Третий комментарий']
        assert sorted(comment_texts) == sorted(expected_texts)

    def test_comment_add_different_users(self, client, post):
        """Тест добавления комментариев разными пользователями"""
        users = UserFactory.create_batch(3)

        comments_data = [
            {'content': f'Комментарий от {user.username}', 'post_id': post.id}
            for user in users
        ]
        # Каждый пользователь добавляет свой комментарий
        for user, comment_data in zip(users, comments_data):
            client.force_login(user)
            response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)
            assert response.status_code == 302
        # Проверяем, что все комментарии были созданы с правильными авторами
        comments = Comment.objects.filter(post=post)
        assert comments.count()

        for comment in comments:
            assert comment.author in users

    def test_comment_add_missing_post_id(self, authenticated_client):
        """Тест добавления комментария без указания snippet_id"""
        client, user = authenticated_client
        # Отправляем POST запрос, не указав snippet_id
        response = client.post(reverse('posts:add_comment', args=[9999]), {'content': 'simple text'})
        assert response.status_code == 404
        # Проверяем, что комментарий не был создан
        assert Comment.objects.count() == 0

    def test_comment_add_long_text(self, authenticated_client, post):
        client, user = authenticated_client
        long_text = 'Очень длинный комментарий .' * 100  # Создаем длинный текст 2600
        comment_data = {
            'content': long_text,
            'post_id': post.id
        }
        response = client.post(reverse('posts:add_comment', args=[post.id]), comment_data)
        assert response.status_code == 302
        assert response.url == reverse('posts:post_detail', args=[post.id])

        # Проверяем, что комментарий был создан с полным текстом
        comment = Comment.objects.filter(post=post).first()
        assert comment is not None
        assert len(comment.content) == len(long_text)


def add_messages_and_session_to_request(request):
    # Attach session for messages to work correctly
    middleware = SessionMiddleware(lambda r: None)  # Mock the get_response callable
    middleware.process_request(request)
    request.session.save()  # Ensure a session key is generated

    # Attach message storage
    setattr(request, '_messages', FallbackStorage(request))


@pytest.mark.django_db
class TestIndexPage:
    def test_index(self):
        client = Client()
        response = client.get(reverse('home'))

        assert response.status_code == 200
        assert response.context['pagename'] == 'Chatty'


@pytest.mark.django_db
class TestPostPage:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_guest_user(self):
        request = self.factory.get(reverse('posts:create_post'))
        request.user = AnonymousUser()
        response = create_post(request)

        assert response.status_code == 302

    def test_auth_user(self):
        request = self.factory.get(reverse('posts:create_post'))
        user = User.objects.create_user(
            username="testuser",
            email="user@example.com",
            password="testuser123"
        )
        request.user = user
        response = create_post(request)

        assert response.status_code == 200

    def test_post_form_data(self):
        form_data = {
            'title': 'Test Post Title',
            'content': 'This is a test post content.',
            'public': True,
        }
        user = User.objects.create_user(
            username="testuser",
            email="username@example.com",
            password="testuser123"
        )
        request = self.factory.post(reverse('posts:create_post'), form_data)
        request.user = user
        add_messages_and_session_to_request(request)
        response = create_post(request)
        print(response.status_code)
        print(response.content)

        post = Post.objects.latest('id')

        assert response.status_code == 302
        assert post.title == form_data['title']
        assert post.content == form_data['content']
        assert post.public == form_data['public']


@pytest.mark.django_db
class TestPostDeletePage:
    def setup_method(self):
        self.client = Client()

    def test_delete_not_existing(self):
        user = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testuser123"
        )
        self.client.login(username="testuser2", password="testuser123")
        response = self.client.get(reverse('posts:delete_post', kwargs={'post_id': 2}))

        assert response.status_code == 404

    def test_delete(self):
        user = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testuser123"
        )
        post = Post.objects.create(
            title="For delete",
            content="test content",
            author=user
        )
        self.client.login(username="testuser2", password="testuser123")
        response = self.client.get(reverse('posts:delete_post', args=[post.id]))

        assert response.status_code == 302
        assert Post.objects.count() == 0

    def tset_delete_not_auth(self):
        user = User.objects.create_user(
            username='testuser3',
            email='testuser3@example.com',
            password='testuser123'
        )
        post = Post.objects.create(
            title='For delete',
            content='testcontent',
            author=user
        )
        response = self.client.get(reverse('posts:delete_post', args=[post.id]))

        assert response.status_code == 403


@pytest.mark.django_db
class TestPostPage:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="user@example.com",
            password="testuser"
        )
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@example.com",
            password="testuser1"
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@example.com",
            password="tastuser2"
        )
        # Создаем множество тестовых постов для более надежных тестов
        self.posts = []
        # посты первого пользователя
        self.posts.extend([
             Post.objects.create(
                 title="Hello world",
                 content="Content1",
                 public=True,
                 author=self.user
             ),
            Post.objects.create(
                title="Title2",
                content="Content2",
                public=True,
                author=self.user
            ),
            Post.objects.create(
                title="Title3",
                content="Content3",
                public=True,
                author=self.user
            ),
            Post.objects.create(
                title="Title4",
                content="Content4",
                public=True,
                author=self.user
            ),
            Post.objects.create(
                title="Title5",
                content="Content5",
                public=True,
                author=self.user
            ),
        ])
        # посты второго пользователя
        self.posts.extend([
            Post.objects.create(
                title="Title1",
                content="Content1",
                public=True,
                author=self.user1
            ),
            Post.objects.create(
                title="Title2",
                content="Content2",
                public=True,
                author=self.user1
            ),
            Post.objects.create(
                title="Title3",
                content="Content3",
                public=True,
                author=self.user1
            )
        ])
        # посты третьего пользователя
        self.posts.extend([
            Post.objects.create(
                title="Title1",
                content="Content1",
                public=True,
                author=self.user2
            ),
            Post.objects.create(
                title="Title2",
                content="Content2",
                public=True,
                author=self.user2
            ),
            Post.objects.create(
                title="Title3",
                content="Content3",
                public=True,
                author=self.user2
            )
        ])

    def test_my_posts_authenticated_user(self):
        """Тест для просмотра своих постов авторизованным пользователем"""
        self.client.login(username="testuser", password="testuser")
        response = self.client.get('/posts/my/')

        assert response.status_code == 200
        assert response.context['pagename'] == "Мои посты"
        # Проверяем, что видны только посты текущего пользователя
        user_posts = [p for p in self.posts if p.author == self.user]
        assert len(response.context['posts']) == len(user_posts)

    def test_my_posts_anonymous_user(self):
        """Тест для просмотра своих постов неавторизованным пользователем"""
        response = self.client.get('/posts/my/')

        assert response.status_code == 403

    def test_all_posts_authenticated_user(self):
        """Тест для просмотра всех постов авторизованным пользователем"""
        num_posts_on_page = 5
        self.client.force_login(self.user)
        response = self.client.get('/posts/', {'num_posts_on_page': num_posts_on_page})

        assert response.status_code == 200
        assert response.context['pagename'] == "Просмотр постов"

        public_posts = [p for p in self.posts if p.public]
        private_qwn_posts = [p for p in self.posts if not p.public and p.author == self.user]
        expected_count = len(public_posts)+len(private_qwn_posts)
        if expected_count > num_posts_on_page:
            expected_count = num_posts_on_page
        assert len(response.context['posts']) == expected_count

    def test_all_posts_anonymous_user(self):
        """Тест для просмотра всех постов неавторизованным пользователем"""
        num_posts_on_page = 5
        response = self.client.get('/posts/', {'num_posts_on_page': num_posts_on_page})
        assert response.status_code == 200
        assert response.context['pagename'] =="Просмотр постов"

        public_posts = [p for p in self.posts if p.public]
        count = len(public_posts)
        if count > num_posts_on_page:
            count = num_posts_on_page
        assert len(response.context['posts']) == count

    def test_post_with_search(self):
        """Тест поиска постов"""
        self.client.force_login(self.user)
        response = self.client.get('/posts/?search=Hello')

        assert response.status_code ==200
        # Проверяем, что найдены посты с "Hello" в названии или контенте
        found_posts = response.context['posts']
        assert len(found_posts) > 0
        for post in found_posts:
            assert "Hello" in post.title or "Hello" in post.content
