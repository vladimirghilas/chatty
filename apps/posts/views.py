import json
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import PostForm, CommentForm
from .models import Post, User, Comment, Notification, LikeDislike, Subscription
from django.contrib import messages
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


# Create your views here.

def posts_list(request, my_posts=None, number_of_posts=5):
    author_id = request.GET.get("author")

    # --- Определяем, какие посты показывать ---
    if my_posts:
        if not request.user.is_authenticated:
            raise PermissionDenied
        pagename = "Мои посты"
        posts_list = (
            Post.with_likes_count()
            .filter(author=request.user)
            .select_related("author")
            .annotate(num_comments=Count("comments", distinct=True))
        )
    elif author_id:
        posts_list = (
            Post.with_likes_count()
            .filter(author_id=author_id, public=True)
            .select_related("author")
            .annotate(num_comments=Count("comments", distinct=True))
        )
        pagename = f'Посты пользователя {User.objects.get(id=author_id).username}'
    else:
        pagename = "Просмотр постов"
        if request.user.is_authenticated:
            posts_list = (
                Post.with_likes_count()
                .filter(Q(public=True) | Q(public=False, author=request.user))
                .select_related("author")
                .annotate(num_comments=Count("comments", distinct=True))
            )
        else:
            posts_list = (
                Post.with_likes_count()
                .filter(public=True)
                .select_related("author")
                .annotate(num_comments=Count("comments", distinct=True))
            )

    # --- Поиск ---
    search = request.GET.get('search', '')
    if search and search.lower() != 'none':
        posts_list = posts_list.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )

    # --- Сортировка ---
    sort = request.GET.get('sort', 'updated_at')
    if sort:
        posts_list = posts_list.order_by(sort)

    # --- Пагинация ---
    paginator = Paginator(posts_list, number_of_posts)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    # --- Левый сайдбар: Топ-5 популярных постов с likes/dislikes/num_comments ---
    top_posts = (
        Post.with_likes_count()
        .filter(public=True)
        .select_related("author")
        .annotate(num_comments=Count("comments", distinct=True))
        .order_by('-views_count')[:5]
    )

    # --- Правый сайдбар: последние 5 зарегистрированных пользователей ---
    users = User.objects.all().order_by('-date_joined')[:5]

    context = {
        'pagename': pagename,
        'posts': posts,
        'search': search,
        'sort': sort,
        'top_posts': top_posts,
        'users': users,
    }

    return render(request, 'posts_list.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            messages.success(request, "Пост успешно создан")
            return redirect('posts:post_detail', post_id=new_post.id)
    else:
        form = PostForm()
    context = {
        'pagename': "Создать новый пост",
        'form': form,
    }
    return render(request, 'create_post.html', context)


def post_detail(request, post_id, number_of_comments=2):
    post = get_object_or_404(Post.with_likes_count(), id=post_id)
    post.views_count = F('views_count') + 1
    post.save(update_fields=['views_count'])
    post.refresh_from_db(fields=['views_count'])
    comments_list = Comment.with_likes_count().filter(post=post)
    comment_form = CommentForm()
    subscribed_ids = []
    if request.user.is_authenticated:
        subscribed_ids = request.user.subscriptions.all().values_list('subscribed_to', flat=True)

    paginator = Paginator(comments_list, number_of_comments)
    page_number = request.GET.get('page')
    comments = paginator.get_page(page_number)

    back_page = request.GET.get('list_page', 1)
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'updated_at')

    context = {
        'post': post,
        'form': comment_form,
        'comments': comments,
        'subscribed_ids': subscribed_ids,
        'back_url': f"{reverse('posts:posts_list')}?page={back_page}&search={search}&sort={sort}"

    }
    return render(request, 'post_detail.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            print(f"post_id = {post_id!r}")
            form.save()
            return redirect('posts:post_detail', post.id)
    else:
        form = PostForm(instance=post)

    context = {
        'pagename': "Редактировать пост",
        'form': form,
        'post': post,
    }

    return render(request, 'edit_post.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.error(request, "У вас нет прав для удаления этого поста")
        return redirect('posts:posts_list')
    post.delete()
    messages.success(request, f'Post "{post.title}" was deleted.')
    return redirect('posts:posts_list')


# CREATE comment
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():  # <- важно, форма должна быть валидной
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()  # <- без этого комментарий не сохранится
            messages.success(request, 'Комментарий добавлен!')
        else:
            messages.error(request, 'Ошибка при добавлении комментария!')

        return redirect('posts:post_detail', post_id=post.id)

    return redirect('posts:post_detail', post_id=post.id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем, является ли пользователь автором комментария или администратором
    if request.user != comment.author and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для удаления этого комментария.")
        return redirect('posts:posts_list')  # или на страницу поста

    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Комментарий успешно удалён.")
        return redirect('posts:posts_list')  # или на страницу поста

    return render(request, 'post_detail.html', {'comment': comment})


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'notifications.html', context)


@login_required
def mark_read_notifications(request, notif_id):
    # Получаем уведомление для текущего пользователя
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)

    # Отмечаем уведомление как прочитанное
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    # Получаем правильный post_id в зависимости от типа уведомления
    if hasattr(notification, 'post') and notification.post:
        post_id = notification.post.id
    elif hasattr(notification, 'comment') and notification.comment:
        post_id = notification.comment.post.id
    else:
        # fallback, если уведомление не связано с постом
        return redirect('homepage')

    # Редирект на страницу поста
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def unread_notifications_count(request):
    import time

    max_wait_time = 10
    check_interval = 1
    last_count = int(request.GET.get('last_count', 0))
    start_time = time.time()
    unread_count = 0

    while time.time() - start_time < max_wait_time:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        logger.info(f"Unread: {unread_count}")
        if unread_count > last_count:
            return JsonResponse({
                'success': True,
                'unread_count': unread_count,
                'timestamp': str(datetime.now())
            })

        time.sleep(check_interval)
    return JsonResponse({
        'success': True,
        'unread_count': unread_count,
        'timestamp': str(datetime.now())
    })


def is_authenticated(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_authenticated': True})
    else:
        return JsonResponse({'is_authenticated': False})


@login_required
@require_POST
def add_comment_like(request):
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        vote = data.get('vote')  # 1 = like, -1 = dislike

        comment = get_object_or_404(Comment, id=comment_id)
        comment_type = ContentType.objects.get_for_model(Comment)

        existing_vote, created = LikeDislike.objects.get_or_create(
            user=request.user,
            content_type=comment_type,
            object_id=comment_id,
            defaults={'vote': vote}
        )

        if not created:
            if existing_vote.vote == vote:
                existing_vote.delete()
            else:
                existing_vote.vote = vote
                existing_vote.save()

        comment_with_counts = Comment.with_likes_count().get(id=comment_id)

        response_data = {
            'success': True,
            'likes_count': comment_with_counts.likes_count,
            'dislikes_count': comment_with_counts.dislikes_count,
        }
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def add_post_like(request):
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        vote = data.get('vote')

        post = Post.objects.get(id=post_id)
        content_type = ContentType.objects.get_for_model(Post)

        existing_vote, created = LikeDislike.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=post_id,
            defaults={'vote': vote}
        )

        if not created:
            if existing_vote.vote == vote:
                existing_vote.delete()
            else:
                existing_vote.vote = vote
                existing_vote.save()

        post_like_counts = Post.with_likes_count().get(id=post_id)

        response_data = {
            'success': True,
            'likes_count': post_like_counts.likes_count,
            'dislikes_count': post_like_counts.dislikes_count
        }
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def toggle_subscription(request, user_id, post_id):
    """Подписка / отписка на пользователя"""
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('posts:post_detail', post_id=post_id)

    subscription, created = Subscription.objects.get_or_create(
        user=request.user, subscribed_to=target_user
    )

    if not created:
        subscription.delete()  # отписка

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def feed_view(request):
    followers = User.objects.filter(subscriptions__subscribed_to=request.user).distinct()
    subscriptions = User.objects.filter(followers__user=request.user).distinct()

    return render(request, "feed.html", {
        "followers": followers,  # кто на меня подписан
        "subscriptions": subscriptions  # на кого я подписан
    })
