import time

from behave import given, when, then

from django.contrib.auth.models import User, Group

from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument


@given("a logged-in facility manager")
def given_a_logged_in_facility_manager(context):
    """
    :type context: behave.runner.Context
    """
    user = User.objects.create_user(  # nosec
        username="facilitymanager",
        password="facilitypass",
        email="facilitymanager@example.com",
        first_name="Facility",
        last_name="Manager",
    )
    group = Group.objects.create(name="Test Facility Managers")
    user.groups.add(group)
    facility = Facility.objects.create(name="Test Facility", manager_group=group)
    instrument = Instrument.objects.create(facility=facility, name="Test Instrument")
    dataset = Dataset.objects.create(description="Test Dataset", instrument=instrument)
    datafile = DataFile.objects.create(
        filename="testfile.txt", size=12345, md5sum="bogus", dataset=dataset
    )
    context.browser.get(context.base_url + "/login/")
    username_field = context.browser.find_element_by_id("id_username")
    username_field.send_keys(user.username)
    password_field = context.browser.find_element_by_id("id_password")
    password_field.send_keys("facilitypass")
    login_form = context.browser.find_element_by_id("login-form")
    login_form.submit()


@when("they open the facility overview url")
def they_open_the_facility_overview_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/facility/overview/")


@then("they see the facility overview page")
def they_see_the_facility_overview_page(context):
    """
    :type context: behave.runner.Context
    """
    max_retries = 30
    retries = 0
    progress_bar = context.browser.find_element_by_css_selector("div.progress")
    while progress_bar.is_displayed() and retries < max_retries:
        time.sleep(0.1)
        retries += 1

    # We can't use the jQuery.active method to determine if the AJAX has
    # finished loading, because this is an AngularJS page.  The progress bar
    # method above works most of the time, but occasionally we see an error
    # suggesting that this method didn't wait long enough for the Facility
    # Overview page to load, so we'll give it some more time to finish loading:
    time.sleep(0.5)

    h2 = context.browser.find_element_by_tag_name("h2")
    context.test.assertEqual(h2.get_attribute("innerHTML"), "Test Facility")

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
