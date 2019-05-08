import time

from behave import when, then

from selenium.common.exceptions import NoSuchElementException


@when("they click the Add New dataset button")
def they_click_add_new_dataset_btn(context):
    """
    :type context: behave.runner.Context
    """
    add_new_btn = context.browser.find_element_by_id("add-dataset")
    add_new_btn.click()


@then("they see the dataset creation form")
def they_see_dataset_form(context):
    """
    :type context: behave.runner.Context
    """
    try:
        create_dataset_form = \
            context.browser.find_element_by_id("add-or-edit-dataset-form")
        found_create_dataset_form = True
    except NoSuchElementException:
        found_create_dataset_form = False
    context.test.assertTrue(found_create_dataset_form)


@when("they fill in the Add Dataset form and click Save")
def fill_in_add_dataset_form_and_save(context):
    """
    :type context: behave.runner.Context
    """
    title_input = context.browser.find_element_by_css_selector(
        "input[name='description']")
    title_input.send_keys("new dataset1")
    save_button = context.browser.find_element_by_css_selector("button[type='submit']")
    save_button.click()


@then("a new dataset is created")
def a_new_dataset_is_created(context):
    """
    :type context: behave.runner.Context
    """
    title_span = context.browser.find_element_by_css_selector(
        "span[property='dc:title']")
    context.test.assertEqual(
        title_span.get_attribute('innerHTML'),
        "new dataset1")

    console_errors = []
    for error in context.browser.get_log('browser'):
        console_errors.append(error)
    context.test.assertEqual(
        len(console_errors), 0, str(console_errors))


@when("they open the experiment url")
def they_open_the_exp_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/experiment/view/1/")


@then("they see the newly created dataset")
def they_see_newly_created_dataset(context):
    """
    :type context: behave.runner.Context
    """
    ajax_complete = bool(
        context.browser.execute_script("return jQuery.active == 0"))
    while not ajax_complete:
        time.sleep(0.1)
        ajax_complete = bool(
            context.browser.execute_script("return jQuery.active == 0"))
    # The ajax-loaded "share.html" experiment tab loads some of its content via ajax
    # so we'll give it some time to finish loading:
    time.sleep(0.5)
    dataset_link = context.browser.find_element_by_css_selector("a.dataset-link")
    context.test.assertIn("new dataset", dataset_link.get_attribute("innerHTML"))
