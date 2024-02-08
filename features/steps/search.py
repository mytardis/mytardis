from behave import when, then


@when("they open the search url")
def they_open_the_search_url(context):
    """
    :type context: behave.runner.Context
    """
    context.browser.get(context.base_url + "/apps/search/")


@then("they see the search page")
def they_see_the_search_page(context):
    """
    :type context: behave.runner.Context
    """
    search_input = context.browser.find_element_by_css_selector(
        "input[name=simple_search_text]"
    )

    context.test.assertEqual(
        search_input.get_attribute("placeholder"),
        "Search for Experiments, Datasets, Datafiles",
    )

    console_errors = []
    for entry in context.browser.get_log("browser"):
        if entry["level"] != "WARNING":
            console_errors.append(entry)
    context.test.assertEqual(len(console_errors), 0, str(console_errors))
