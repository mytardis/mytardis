"""
Setting up BDD with Spliner/Selenium and Behave
"""

from django.core import management
from npm.finders import npm_install
from splinter.browser import Browser


def before_all(context):

    npm_install()

    browser = context.config.userdata.get('browser', 'phantomjs')
    context.browser = Browser(browser)

    # When we're running with PhantomJS we need to specify the window size.
    # This is a workaround for an issue where PhantomJS cannot find elements
    # by text - see: https://github.com/angular/protractor/issues/585
    if context.browser.driver_name == 'PhantomJS':
        context.browser.driver.set_window_size(1280, 1024)


def before_scenario(context, scenario):
    # Reset the database before each scenario
    # This means we can create, delete and edit objects within an
    # individual scenerio without these changes affecting our
    # other scenarios
    management.call_command('flush', verbosity=0, interactive=False)


def after_all(context):
    # Explicitly quits the browser, otherwise it won't once tests are done
    context.browser.quit()
    context.browser = None


def before_feature(context, feature):
    pass
