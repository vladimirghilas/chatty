from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Post
from django.contrib import messages


# Create your views here.
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'post_list.html', {'posts': posts})

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
