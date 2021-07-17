import time

from behave import when, then

from selenium.common.exceptions import NoSuchElementException

from tardis.tardis_portal.models.experiment import Experiment

from wait import wait_for_jquery


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
    wait_for_jquery(context)
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
    context.browser.execute_script("arguments[0].scrollIntoView();", save_button)
    context.browser.execute_script("arguments[0].click();", save_button)


@then("a new experiment is created")
def a_new_exp_is_created(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)
    created_alert = context.browser.find_element_by_css_selector(
        "span[class='message']")
    context.test.assertEqual(
        created_alert.get_attribute("innerHTML"),
        "Experiment Created")

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry['level'] != 'WARNING':
            console_errors.append(entry)
    context.test.assertEqual(
        len(console_errors), 0, str(console_errors))


@then("they see the newly created experiment")
def new_exp_in_mydata_view(context):
    """
    :type context: behave.runner.Context
    """
    explink = context.browser.find_element_by_css_selector("a.explink")
    context.test.assertIn("test exp1", explink.get_attribute("innerHTML"))


@when("they click the Metadata link")
def they_click_the_metadata_link(context):
    """
    :type context: behave.runner.Context
    """
    metadata = context.browser.find_element_by_css_selector("a[title='Metadata']")
    metadata.click()


@then("the experiment metadata tab content is shown")
def exp_metadata_tab_content_is_shown(context):
    """
    :type context: behave.runner.Context
    """
    # The "Add Experiment Metadata" button should be shown:
    context.browser.find_element_by_css_selector("a.add-metadata[title='Add']")


@when("they click the Sharing link")
def they_click_the_sharing_link(context):
    """
    :type context: behave.runner.Context
    """
    sharing = context.browser.find_element_by_css_selector("a[title='Sharing']")
    sharing.click()


@then("the experiment sharing tab content is shown")
def exp_sharing_tab_content_is_shown(context):
    """
    :type context: behave.runner.Context

    Use find_element (with implicitly_wait set in features/environment.py)
    to ensure we can find the expected elements
    """
    context.browser.find_element_by_css_selector("div.sharing-sections")
    context.browser.find_element_by_css_selector("div.access_list_user")


@when("they click the Change Public Access link")
def they_click_the_change_public_access_button(context):
    """
    :type context: behave.runner.Context
    """
    public_access_link = context.browser.find_element_by_class_name("public_access_button")
    public_access_link.click()


@then("they see the Change Public Access form")
def they_see_the_change_public_access_form(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)
    exp_id = Experiment.objects.get(title="test exp1").id
    form = context.browser.find_element_by_css_selector("form.experiment-rights")
    context.test.assertIn(
        "post", form.get_attribute("method"))
    close_link = context.browser.\
        find_element_by_css_selector("#modal-public-access > div > div > div.modal-header > button > span")
    close_link.click()
    time.sleep(0.5)
