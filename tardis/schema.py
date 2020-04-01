import logging
from importlib import import_module

from graphene import ObjectType, Schema

from tardis.app_config import get_tardis_apps

logger = logging.getLogger(__name__)


combinedQuery = []
combinedMutation = []

apps = [("tardis_portal", "tardis.tardis_portal")] + get_tardis_apps()

for app_name, app in apps:
    try:
        app_schema = import_module("{}.graphql.schema".format(app))
        combinedQuery.append(getattr(app_schema, "tardisQuery"))
        combinedMutation.append(getattr(app_schema, "tardisMutation"))
    except ImportError as e:
        logger.debug("App {} schema import error: {}".format(app_name, str(e)))

class Query(*combinedQuery, ObjectType):
    pass

class Mutation(*combinedMutation, ObjectType):
    pass

schema = Schema(query=Query, mutation=Mutation)
