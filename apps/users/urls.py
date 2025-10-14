from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    path('', views.users_list, name='users_list'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('registration/', views.user_registration, name='registration'),
    path('activate/<int:user_id>/<str:token>/', views.activate_account, name='activate_account'),
    path('resend-activation/', views.resend_activation, name='resend_activation'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
