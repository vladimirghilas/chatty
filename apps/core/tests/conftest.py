import pytest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from apps.core.factories import UserFactory

@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless")# optional
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=service)
    yield driver
    driver.quit()

def test_open_page(browser):
    browser.get('https://@example.com')
    assert "Example" in browser.title

@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return UserFactory()

# @pytest.fixture
# def authenticated_client(client, user):
#     client.force_login(user)
#     return client , user