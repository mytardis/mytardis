import warnings

from tardis.tardis_portal.deprecations import RemovedInMyTardis42Warning


warnings.warn(
   "The mx_views app will be removed in MyTardis 4.2. ",
   RemovedInMyTardis42Warning)
