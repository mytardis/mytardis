from celery.task import task
from tardis.apps.sync.models import SyncedModel

@task(name="tardis.apps.sync.tasks.clock_tick", ignore_result=True)

def clock_tick():
    if SyncedModel.objects.all().count() == 0:
        exp = SyncedModel()
    else:
        exp = SyncedModel.objects.all()[0]

    print exp.state
    exp.state = exp.state.get_next_state(True)
    exp.save()




