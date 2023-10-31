from datetime import datetime
from django.contrib.auth.models import User

from tardis.celery import tardis_app

from .models import Stat, UserStat
from .utils import get_user_stats


@tardis_app.task
def update_user_stats():
    """
    Calculate stats for all users
    """
    today = datetime.now().date()
    metrics = [
        ["datafiles", "datafiles"],
        ["datasets", "datasets"],
        ["experiments", "experiments"],
        ["size", "size"]
    ]
    for k in metrics:
        k.append(Stat.objects.get_or_create(name=k[0])[0])
    users = User.objects.all()
    for user in users:
        data = get_user_stats(user)
        for k in metrics:
            if k[1] in data:
                if k[0] == "size":
                    field = "bigint_value"
                else:
                    field = "int_value"
                UserStat.objects.update_or_create(
                    date=today,
                    user=user,
                    stat=k[2],
                    defaults={
                        field: data[k[1]]
                    })
