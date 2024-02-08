from behave import given, when, then

from django.contrib.auth.models import User

from selenium.common.exceptions import NoSuchElementException


@given("a logged-in admin user")
def given_a_logged_in_admin_user(context):
    """
    :type context: behave.runner.Context
    """
    user = User.objects.create_user(  # nosec
        username="testadmin1",
        password="testadminpass",
        email="testadmin1@example.com",
        first_name="Test",
        last_name="Admin1",
        is_superuser=True,
    )
    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("testadminpass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()


@when("they open the stats url")
def they_open_the_stats_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/stats/")


@then("they see the stats page")
def they_see_the_stats_page(context):
    """
    :type context: behave.runner.Context
    """
    try:
        title = context.browser.find_element_by_css_selector("h1.title")
        found_title = True
    except NoSuchElementException:
        found_title = False
    context.test.assertTrue(found_title)

    context.test.assertEqual(title.get_attribute("innerHTML"), "Stats")

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
