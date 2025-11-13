import pytest
from apps.core.factories import UserFactory
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_task():
    UserFactory(username='Alice')
    user = User.objects.get(username='Alice')

    assert user.username == 'Alice'
