"""
Setting up BDD with Selenium and Behave
"""
from django.conf import settings
from django.core import management
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def before_all(context):

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    capabilities = DesiredCapabilities.CHROME
    capabilities["loggingPrefs"] = {"browser": "SEVERE"}

    context.browser = webdriver.Chrome(
        executable_path="/usr/local/bin/chromedriver",
        chrome_options=chrome_options,
        desired_capabilities=capabilities,
    )
    context.browser.set_page_load_timeout(10)
    context.browser.implicitly_wait(10)
    context.browser.maximize_window()

    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


def before_scenario(context, scenario):
    # Reset the database before each scenario
    # This means we can create, delete and edit objects within an
    # individual scenerio without these changes affecting our
    # other scenarios
    management.call_command("flush", verbosity=0, interactive=False)


def after_all(context):
    # Explicitly quits the browser, otherwise it won't once tests are done
    context.browser.quit()
    context.browser = None


def before_feature(context, feature):
    pass
