from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .models import Post, User, Comment, Notification
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def posts_list(request, my_posts=None, number_of_posts=5):
    query = request.GET.get('q', '')
    author_id = request.GET.get("author")
    if my_posts:
        if not request.user.is_authenticated:
            raise PermissionDenied
        pagename = "Мои посты"
        posts_list = Post.objects.filter(author=request.user).select_related("author")
    elif author_id:
        posts_list = Post.objects.filter(author_id=author_id, public=True)
        pagename = f'Посты пользователя {User.objects.get(id=author_id).username}'
    else:
        pagename = "Просмотр постов"
        if request.user.is_authenticated:
            posts_list = Post.objects.filter(Q(public=True) | Q(public=False, author=request.user)).select_related(
                "author")
        else:
            posts_list = Post.objects.filter(public=True).select_related("author")

    if query:
        posts_list = posts_list.filter(Q(title__icontains=query) | Q(content__icontains=query))

    paginator = Paginator(posts_list.select_related("author"), number_of_posts)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)
    context = {
        'pagename': pagename,
        'posts': posts,
        'query': query
    }
    return render(request, 'posts_list.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
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


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.views_count += 1
    post.save(update_fields=['views_count'])
    comment_form = CommentForm()
    context = {
        'post': post,
        'form': comment_form,
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
        raise PermissionDenied

    if request.method == 'POST':
        post.delete()
        return redirect('posts:posts_list')

    return render(request, 'post_delete.html', {'post': post})


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
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    post_id = notification.post.id
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

def add_comment_like(request):
    ...
