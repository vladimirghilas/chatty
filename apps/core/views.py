from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count
from apps.posts.models import Post, Comment


# Create your views here.

def home_main(request):
    posts = (Post.with_likes_count()
             .select_related("author")
             .annotate(num_comments=Count("comments", distinct=True))
             .order_by('-views_count')[:5])
    users = User.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')[:5]
    context = {
        'posts': posts,
        'users': users,
        'pagename': 'Chatty'
    }
    return render(request, 'home.html', context)
