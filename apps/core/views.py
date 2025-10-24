from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Count
from apps.posts.models import Post


# Create your views here.

def home(request):
    posts = (Post.objects
             .select_related("author")
             .annotate(num_comments=Count("comments"))
             .order_by('-views_count')[:5])
    users = User.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')[:5]
    context = {
        'posts': posts,
        'users': users
    }
    return render(request, 'home.html', context)
