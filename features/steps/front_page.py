from behave import *


@given("an anoonymous user")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.visit(context.base_url)
    assert context.browser.is_text_present('MyTardis')


@when("they open the url")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@then("they see the front page")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass
