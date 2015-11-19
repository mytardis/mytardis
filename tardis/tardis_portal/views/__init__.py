"""
importing all views files here, so that any old code will work as expected,
when importing from tardis.tardis_portal.views
"""
# pylint: disable=W0401,W0614

from tardis.tardis_portal.views.ajax_actions import *
from tardis.tardis_portal.views.ajax_json import *
from tardis.tardis_portal.views.ajax_pages import *
from tardis.tardis_portal.views.authentication import *
from tardis.tardis_portal.views.authorisation import *
from tardis.tardis_portal.views.facilities import *
from tardis.tardis_portal.views.images import *
from tardis.tardis_portal.views.machine import *
from tardis.tardis_portal.views.pages import *
from tardis.tardis_portal.views.parameters import *
from tardis.tardis_portal.views.search import *
from tardis.tardis_portal.views.upload import *
from tardis.tardis_portal.views.utils import *
