import time


def wait_ajax_loaded(context):
    ajax_complete = bool(
        context.browser.execute_script("return jQuery.active == 0"))
    while not ajax_complete:
        time.sleep(0.1)
        ajax_complete = bool(
            context.browser.execute_script("return jQuery.active == 0"))
    time.sleep(0.5)
