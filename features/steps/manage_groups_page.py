import time

from behave import when, then

from selenium.common.exceptions import NoSuchElementException

from wait import wait_for_jquery


@when("they open the manage groups url")
def they_open_the_manage_groups_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/group/groups/")


@then("they see the manage groups page")
def they_see_the_manage_groups_page(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)

    try:
        title = context.browser.find_element_by_css_selector(".page-header h1")
        found_title = True
    except NoSuchElementException:
        found_title = False
    context.test.assertTrue(found_title)

    context.test.assertEqual(title.get_attribute("innerHTML"), "Manage Group Members")

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
