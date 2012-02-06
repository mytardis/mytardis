from celery.task import task
from time import strftime

@task(name="tardis.apps.sync.tasks.clock_tick", ignore_result=True)
def clock_tick():
    print  "The time is: %s" % (strftime("%X %x %Z"))

