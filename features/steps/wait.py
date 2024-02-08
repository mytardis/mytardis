import time


def wait_for_jquery(context):
    jquery_complete = bool(context.browser.execute_script("return jQuery.active == 0"))
    while not jquery_complete:
        time.sleep(0.1)
        jquery_complete = bool(
            context.browser.execute_script("return jQuery.active == 0")
        )
    time.sleep(0.5)
