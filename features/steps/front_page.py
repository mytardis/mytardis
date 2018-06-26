from behave import *


@given("an anonymous user")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url)
    assert 'MyTardis' in context.browser.page_source


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
