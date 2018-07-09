"""
importing all views files here, so that any old code will work as expected,
when importing from tardis.tardis_portal.views
"""
# pylint: disable=W0401,W0614

from .ajax_actions import *
from .ajax_json import *
from .ajax_pages import *
from .authentication import *
from .authorisation import *
from .facilities import *
from .images import *
from .machine import *
from .pages import *
from .parameters import *
from .upload import *
from .utils import *
