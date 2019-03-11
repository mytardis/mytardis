from behave import when, then

from selenium.common.exceptions import NoSuchElementException


@when("they click the Create Experiment button")
def they_click_create_exp_btn(context):
    """
    :type context: behave.runner.Context
    """
    create_exp_btn = context.browser.find_element_by_id("create-experiment")
    create_exp_btn.click()


@then("they see the experiment creation form")
def they_see_exp_form(context):
    """
    :type context: behave.runner.Context
    """
    try:
        create_exp_form = \
            context.browser.find_element_by_id("create_experiment_form")
        found_create_exp_form = True
    except NoSuchElementException:
        found_create_exp_form = False
    context.test.assertTrue(found_create_exp_form)


@when("they fill in the experiment creation form and click Save")
def fill_in_create_exp_and_save(context):
    """
    :type context: behave.runner.Context
    """
    title_input = context.browser.find_element_by_css_selector("input[name='title']")
    title_input.send_keys("test exp1")
    authors_input = context.browser.find_element_by_css_selector("input[name='authors']")
    authors_input.send_keys("Test User1")
    save_button = context.browser.find_element_by_css_selector("button[type='submit']")
    save_button.click()


@then("a new experiment is created")
def a_new_exp_is_created(context):
    """
    :type context: behave.runner.Context
    """
    created_alert = context.browser.find_element_by_css_selector(
        "span[class='message']")
    context.test.assertEqual(
        created_alert.get_attribute('innerHTML'),
        "Experiment Created")


    console_errors = []
    for error in context.browser.get_log('browser'):
        console_errors.append(error)
    context.test.assertEqual(
        len(console_errors), 0, str(console_errors))
