from behave import when, then

from selenium.common.exceptions import NoSuchElementException


@when("they open the My Data url")
def they_open_the_mydata_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/mydata/")


@then("they see the Create Experiment button")
def they_see_the_create_exp_btn(context):
    """
    :type context: behave.runner.Context
    """
    try:
        create_exp_btn = context.browser.find_element_by_id("create-experiment")
        found_create_exp_btn = True
    except NoSuchElementException:
        found_create_exp_btn = False
    context.test.assertTrue(found_create_exp_btn)
