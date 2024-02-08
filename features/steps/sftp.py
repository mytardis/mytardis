from behave import when, then


@when("they open the SFTP index url")
def they_open_the_sftp_index_url(context):
    """
    The SFTP instructions page

    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/apps/sftp/")


@then("they see the SFTP instructions page")
def they_see_the_sftp_instructions_page(context):
    """
    :type context: behave.runner.Context
    """
    h1 = context.browser.find_element_by_css_selector("h1")

    context.test.assertIn(
        "Instructions for file access via SFTP", h1.get_attribute("innerHTML")
    )

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))


@when("they open the SFTP keys url")
def they_open_the_sftp_keys_url(context):
    """
    The SFTP keys page

    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/apps/sftp/keys/")


@then("they see the SFTP keys page")
def they_see_the_sftp_keys_page(context):
    """
    :type context: behave.runner.Context
    """
    h2 = context.browser.find_element_by_css_selector("h2")

    context.test.assertIn("SSH Keys", h2.get_attribute("innerHTML"))

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
