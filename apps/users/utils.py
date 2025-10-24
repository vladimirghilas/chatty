from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse


def send_activation_email(user, request):
    """
    Отправляет email для подтверждения аккаунта
    """
    # Генерируем токен
    token = default_token_generator.make_token(user)

    activation_url = request.build_absolute_uri(
        reverse('users:activate_account', kwargs={'user_id': user.id, 'token': token})
    )

    # Контекст для шаблона
    context = {
        'user': user,
        'activation_url': activation_url,
    }

    # Рендерим HTML версию письма
    html_message = render_to_string('account_activation.html', context)

    # Рендерим текстовую версию письма
    text_message = render_to_string('account_activation.txt', context)

    # Отправляем email
    send_mail(
        subject='Подтверждение аккаунта',
        message=text_message,
        html_message=html_message,
        from_email='noreply@yoursite.com',
        recipient_list=[user.email],
        fail_silently=False,
    )

    return token


def verify_activation_token(user, token):
    """
    Проверяет токен подтверждения
    """
    return default_token_generator.check_token(user, token)