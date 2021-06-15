from behave import given, when, then

from django.contrib.auth.models import User, Group

from tardis.tardis_portal.models.access_control import ExperimentACL
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment

from wait import wait_for_jquery


@given("a logged-in experiment-sharing user")
def given_a_logged_in_experiment_sharing_user(context):
    """
    :type context: behave.runner.Context
    """
    user1 = User.objects.create_user(  # nosec
            username="user1",
            password="user1pass",
            email="user1@example.com",
            first_name="Experiment",
            last_name="Sharer")
    user2 = User.objects.create_user(  # nosec
            username="user2",
            password="user2pass",
            email="user2@example.com",
            first_name="Sharing",
            last_name="Recipient")
    group = Group.objects.create(name="Group1")
    user1.groups.add(group)
    user2.groups.add(group)
    experiment = Experiment.objects.create(
        title="Shared Experiment1", created_by=user1)
    acl = ExperimentACL.objects.create(
        experiment=experiment,
        group=group,
        canRead=True)
    dataset = Dataset.objects.create(description="Shared Dataset")
    dataset.experiments.add(experiment)
    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user2.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("user2pass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()

@when("they open the shared experiments url")
def they_open_the_shared_experiments_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/shared/")

@then("they see the shared experiment")
def exp_in_shared_view(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)
    explink = context.browser.find_element_by_css_selector("a.explink")
    context.test.assertIn("Shared Experiment1", explink.get_attribute("innerHTML"))

@given("a public experiment")
def given_a_public_experiment(context):
    """
    :type context: behave.runner.Context
    """
    user1 = User.objects.create_user(  # nosec
            username="user1",
            password="user1pass",
            email="user1@example.com",
            first_name="Experiment",
            last_name="Creater")
    experiment = Experiment.objects.create(
        title="Public Experiment1", created_by=user1)
    experiment.public_access = Experiment.PUBLIC_ACCESS_FULL
    experiment.save()
    dataset = Dataset.objects.create(description="Public Dataset")
    dataset.experiments.add(experiment)

@when("they open the public experiments url")
def they_open_the_public_experiments_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/public_data/")

@then("they see the public experiment")
def exp_in_public_view(context):
    """
    :type context: behave.runner.Context
    """
    wait_for_jquery(context)
    explink = context.browser.find_element_by_css_selector("a.explink")
    context.test.assertIn("Public Experiment1", explink.get_attribute("innerHTML"))
    dataset_li = context.browser.find_element_by_css_selector(".dataset-list-item")
    context.test.assertIn("Public Dataset", dataset_li.get_attribute("innerHTML"))
