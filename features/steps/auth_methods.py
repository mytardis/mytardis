from behave import given, when, then

from django.contrib.auth.models import User, Permission

from wait import wait_for_jquery


@given("a logged-in user with change user-auth perms")
def given_a_logged_in_user_with_change_user_auth_perms(context):
    """
    Only users with the tardis_portal.change_userauthentication
    permission can access the Link Accounts menu item which
    renders the auth_methods.html template

    :type context: behave.runner.Context
    """
    user = User.objects.create_user(  # nosec
        username="testuser1",
        password="testpass",
        email="testuser1@example.com",
        first_name="Test",
        last_name="User1",
    )
    user.user_permissions.add(
        Permission.objects.get(codename="change_userauthentication")
    )
    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("testpass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()


@when("they open the auth methods url")
def they_open_the_auth_methods_url(context):
    """
    The "Link Accounts" menu item

    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/accounts/manage_auth_methods/")


@then("they see the auth methods page")
def they_see_the_auth_methods_page(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)

    auth_list_div = context.browser.find_element_by_id("authList")

    context.test.assertIn("Local DB", auth_list_div.get_attribute("innerHTML"))

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
