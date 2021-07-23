from tardis.app_config import AbstractTardisAppConfig


class ExperimentPIDConfig(AbstractTardisAppConfig):
    name = "tardis.apps.persistent_identifiers.experiment_pid"
    verbose_name = "experiment_pid"


class DatasetPIDConfig(AbstractTardisAppConfig):
    name = "tardis.apps.persistent_identifiers.dataset_pid"
    verbose_name = "dataset_pid"
