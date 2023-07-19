from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .models import Action, Log
from .signals import event_logged


def log(action, user=None, obj=None, extra=None, request=None):
    enabled_actions = getattr(settings, "EVENTLOG_ACTIONS", [])
    if enabled_actions and action not in enabled_actions:
        return None

    if user is None and request is not None:
        user = request.user

    if user is not None and not user.is_authenticated:
        user = None

    if extra is None:
        extra = {}

    content_type = None
    object_id = None
    if obj is not None:
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk

    if request is not None:
        extra = {**extra, **get_request_data(request)}

    event = Log.objects.create(
        action=Action.objects.get_or_create(name=action)[0],
        user=user,
        content_type=content_type,
        object_id=object_id,
        extra=extra,
    )

    event_logged.send(sender=Log, event=event)

    return event


def get_request_data(request):
    if x_forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
        user_ip = x_forwarded_for.split(",")[0]
    else:
        user_ip = request.META.get("REMOTE_ADDR")
    data = {"ip": user_ip}
    if user_agent := request.META.get("HTTP_USER_AGENT"):
        data["ua"] = user_agent

    if user_name := request.POST.get("username"):
        data["username"] = user_name

    return data
