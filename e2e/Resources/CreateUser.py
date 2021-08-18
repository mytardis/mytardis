from django.contrib.auth.models import User, Permission
from selenium import webdriver


context = webdriver.Chrome()

user = User.objects.create_user(  # nosec
            username="testuser1",
            password="testpass",
            email="testuser1@example.com",
            first_name="Test",
            last_name="User1")
user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))
context.browser.get(context.base_url + "/login/")
username_field = context.browser.find_element_by_id('id_username')
username_field.send_keys(user.username)
password_field = context.browser.find_element_by_id('id_password')
password_field.send_keys("testpass")
login_form = context.browser.find_element_by_id('login-form')
login_form.submit()