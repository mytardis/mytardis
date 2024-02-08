from behave import given, when, then

from django.contrib.auth.models import User

from tardis.tardis_portal.models.access_control import ExperimentACL
from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment

from wait import wait_for_jquery


@given("a logged-in user with dataset access")
def given_a_logged_in_user_with_dataset_access(context):
    """
    :type context: behave.runner.Context
    """
    user = User.objects.create_user(  # nosec
        username="testuser",
        password="testuserpass",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
    )
    experiment = Experiment.objects.create(title="Test Experiment1", created_by=user)
    acl = ExperimentACL.objects.create(experiment=experiment, user=user, canRead=True)
    dataset = Dataset.objects.create(description="Test Dataset")
    dataset.experiments.add(experiment)
    datafile1 = DataFile.objects.create(
        filename="testfile1.txt", size=12345, md5sum="bogus", dataset=dataset
    )
    datafile2 = DataFile.objects.create(
        filename="testfile2.txt", size=123456, md5sum="bogus2", dataset=dataset
    )
    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("testuserpass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()


@when("they open the dataset view url")
def they_open_the_dataset_view_url(context):
    """
    :type context: behave.runner.Context
    """
    dataset_id = Dataset.objects.first().id
    context.browser.get(context.base_url + "/dataset/%s" % dataset_id)
    wait_for_jquery(context)

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))


@then("they see the dataset with files")
def they_see_the_dataset_with_files(context):
    """
    :type context: behave.runner.Context
    """
    span = context.browser.find_element_by_css_selector('span[property="dc:title"]')
    context.test.assertEqual("Test Dataset", span.get_attribute("innerHTML"))

    datafiles_tbody = context.browser.find_element_by_css_selector(
        "table.datafiles tbody"
    )
    context.test.assertIn("testfile1.txt", datafiles_tbody.get_attribute("innerHTML"))
    context.test.assertIn("testfile2.txt", datafiles_tbody.get_attribute("innerHTML"))
    """
    datafile_list_tab = context.browser.find_element_by_id("datafile-list")
    datafile_list_tab.click()
    datafile_info_toggle = context.browser.find_element_by_css_selector(".datafile-info-toggle")
    datafile_info_toggle.click()
    no_metadata_msg = context.browser.find_element_by_css_selector(".datafile_parameters em")
    context.test.assertIn("There is no metadata for this file", no_metadata_msg.get_attribute("innerHTML"))
    """
