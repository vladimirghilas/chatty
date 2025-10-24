from django.urls import path
from . import views

app_name = "posts"
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.posts_list, name='posts_list'),  # ← добавили этот
    path('my', views.posts_list, {'my_posts': True}, name='my_posts'),  # ← добавили этот
    path('create', views.create_post, name='create_post'),
    path('<int:post_id>', views.post_detail, name='post_detail'),
    path('<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]
