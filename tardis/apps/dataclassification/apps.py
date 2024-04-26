from tardis.app_config import AbstractTardisAppConfig
from tardis.apps.dataclassification.enumerators import DataClassificationAppEnum

class DataClassificationConfig(AbstractTardisAppConfig):
    name = DataClassificationAppEnum.NAME.value
    verbose_name = DataClassificationAppEnum.VERBOSE_NAME.value
