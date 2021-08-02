from django.contrib.auth.models import AnonymousUser

from tardis.tardis_portal.api import MyTardisModelResource

from .models import UserStat
from .utils import get_user_last

class StatsAppResource(MyTardisModelResource):
    """
    API endpoint for user stats
    """
    class Meta(MyTardisModelResource.Meta):
        resource_name = "stats"
        list_allowed_methods = ["get"]
        detail_allowed_methods = []

    def obj_get_list(self, bundle, **kwargs):
        return []

    def get_list(self, request, **kwargs):
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        if isinstance(request.user, AnonymousUser):
            rsp = {
                "message": "Anonymous stats are coming soon."
            }
        else:
            rsp = {
                "user": {
                    "id": request.user.id,
                },
                "last": {
                    "login": request.user.last_login
                },
                "total": {}
            }

            rsp["last"].update(get_user_last(request.user))

            metrics = ["experiments", "datasets", "datafiles", "size"]
            for k in metrics:
                data = UserStat.objects.filter(
                    user=request.user,
                    stat__name=k
                ).order_by("-date")[:1]
                if len(data) != 0:
                    data = data[0].__dict__
                    if k == "size":
                        v = "bigint_value"
                    else:
                        v = "int_value"
                    rsp["total"][k] = {
                        "value": data[v],
                        "date": data["date"]
                    }

        return self.create_response(request, rsp)
