from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm, UserEditForm, ProfileForm
from django.contrib import messages
from .utils import send_activation_email, verify_activation_token
from django.core.paginator import Paginator


# Create your views here.

def users_list(request, number_of_users=5):
    query = request.GET.get('q', '')
    users_list = User.objects.all().order_by("username")
    if query:
        users_list = users_list.filter(Q(username__icontains=query) | Q(email__icontains=query))

    paginator = Paginator(users_list, number_of_users)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        'users': page_obj,
        'query': query
    }
    return render(request, 'users/users_list.html', context)


def user_registration(request):
    if request.method == 'GET':
        form = UserRegistrationForm()
        context = {
            'form': form
        }
        return render(request, 'users/registration.html', context)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            send_activation_email(user, request)
            messages.success(
                request,
                f'Пользователь "{user.username}" успешно зарегистрирован. Проверьте ваш email для подтверждения аккаунта.')
            return redirect('home')
        else:
            context = {
                'form': form
            }
        return render(request, 'users/registration.html', context)


def activate_account(request, user_id, token):
    """
        Подтверждение аккаунта пользователя по токену
        """
    try:
        user = User.objects.get(id=user_id)
        if user.is_active:
            messages.info(request, 'Ваш аккаунт уже подтвержден.')
            return redirect('home')

        if verify_activation_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request,
                             'Ваш аккаунт успешно подтвержден! Теперь вы можете войти в систему.')
            return redirect('home')
        else:
            messages.error(request,
                           'Недействительная ссылка для подтверждения. Возможно, она устарела.')
            return redirect('home')
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('home')


def resend_activation(request):
    if request.method == 'GET':
        return render(request, 'users/resend_email.html')
    elif request.method == 'POST':
        email = request.POST.get('email')
        # TODO:
        user = User.objects.get(email=email)
        try:
            send_activation_email(user, request)
            messages.success(request, f'Email для подтверждения аккаунта отправлен повторно. Проверьте ваш email.')
        except:
            messages.error(request, f'ask your administration')
        return redirect('home')
    else:
        raise Http404


# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             messages.success(request, f'Добро пожаловать, {user.username}!')
#             return redirect('home')
#         else:
#             messages.error(request, 'Неверное имя пользователя или пароль!')
#     return render(request, 'users/login.html')

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'users/profile_view.html', {'profile': profile})


@login_required
def profile_edit(request):
    profile = request.user.profile  # получаем профиль текущего пользователя

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлён")
        else:
            messages.error(request, "Ошибка при обновлении профиля")
    else:
        # Важно: при GET-запросе передаём instance=profile
        form = ProfileForm(instance=profile)

    # Передаём profile в контекст, чтобы шаблон мог показать аватар
    return render(request, 'users/profile_edit.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Пользователь {user.username} обновлен!')
            return redirect('users_list')
        else:
            messages.error(request, 'Форма содержит ошибки!')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'users/edit_user.html', {'form': form, 'user': user})


@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'Пользователь {user.username} удален!')
        return redirect('users_list')
    return render(request, 'users/confirm_delete.html', {'user': user})
