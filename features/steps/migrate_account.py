from behave import given, when, then

from django.contrib.auth.models import User, Permission


@given("a logged-in user with account migration perms")
def given_a_logged_in_user_with_account_migration_perms(context):
    """
    Only users with the add_openidusermigration
    permission can access the Migrate My Account menu item which
    renders the migrate_accounts.html template

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
        Permission.objects.get(codename="add_openidusermigration")
    )

    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("testpass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()


@when("they open the account migration url")
def they_open_the_account_migration_url(context):
    """
    The "Migrate My Account" menu item

    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/apps/openid-migration/migrate-accounts/")


@then("they see the Migrate My Account page")
def they_see_the_migrate_my_account_page(context):
    """
    :type context: behave.runner.Context
    """
    legend = context.browser.find_element_by_css_selector("legend")

    context.test.assertIn("Migrate My Account", legend.get_attribute("innerHTML"))

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
