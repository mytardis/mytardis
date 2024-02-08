from behave import given, when, then

from selenium.common.exceptions import NoSuchElementException


@when("they open the about url")
def they_open_the_about_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/about/")


@then("they see the about page")
def they_see_the_about_page(context):
    """
    :type context: behave.runner.Context
    """
    try:
        title = context.browser.find_element_by_css_selector("h1.title")
        found_title = True
    except NoSuchElementException:
        found_title = False
    context.test.assertTrue(found_title)

    context.test.assertEqual(title.get_attribute("innerHTML"), "About MyTardis")

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
