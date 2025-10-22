from IPython.core.release import author
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Post, User
from django.contrib import messages


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
            posts_list = Post.objects.filter(Q(public=True) | Q(public=False, author=request.user)).select_related("author")
        else:
            posts_list = Post.objects.filter(public=True).select_related("author")

    if query:
        posts_list = posts_list.filter(Q(title__icontains=query) | Q(content__icontains=query))

    paginator = Paginator(posts_list.select_related("author"),number_of_posts)
    page_number= request.GET.get("page")
    posts=paginator.get_page(page_number)
    context = {
        'pagename': pagename,
        'posts': posts,
        'query': query
    }
    return render(request, 'posts_list.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Пост успешно создан")
            return redirect('posts:post_detail', post_id=post.id)
    else:
        form = PostForm()

    return render(request, 'create_post.html', {'form': form})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.views_count += 1
    post.save(update_fields=['views_count'])
    return render(request, 'post_detail.html', {'post': post})
