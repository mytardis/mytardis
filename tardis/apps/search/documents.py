import logging
from django.conf import settings

from django.contrib.auth.models import User
from elasticsearch_dsl import analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from tardis.tardis_portal.models import (
    Experiment,
    Dataset,
    DataFile,
    Instrument,
    ExperimentACL,
    DatasetACL,
    DatafileACL,
    ParameterName,
    ExperimentParameter,
    ExperimentParameterSet,
    DatasetParameter,
    DatasetParameterSet,
    DatafileParameter,
    DatafileParameterSet,
    Schema,
    DataFileObject,
)

from tardis.apps.projects.models import (
    Project,
    ProjectParameter,
    ProjectParameterSet,
    ProjectACL,
)


logger = logging.getLogger(__name__)


elasticsearch_index_settings = getattr(
    settings,
    "ELASTICSEARCH_DSL_INDEX_SETTINGS",
    {"number_of_shards": 1, "number_of_replicas": 0},
)
elasticsearch_parallel_index_settings = getattr(
    settings, "ELASTICSEARCH_PARALLEL_INDEX_SETTINGS", {}
)

analyzer = analyzer(
    "analyzer",
    tokenizer="standard",
    filter=["lowercase", "stop", "word_delimiter_graph"],
)


def generic_acl_structure():
    return fields.NestedField(
        properties={
            "pluginId": fields.KeywordField(),
            "entityId": fields.KeywordField(),
        }
    )


def generic_parameter_structure():
    return fields.NestedField(
        properties={
            "string": fields.NestedField(
                properties={
                    "pn_id": fields.KeywordField(),
                    "pn_name": fields.KeywordField(),
                    "value": fields.TextField(),
                    "sensitive": fields.BooleanField(),
                }
            ),
            "numerical": fields.NestedField(
                properties={
                    "pn_id": fields.KeywordField(),
                    "pn_name": fields.KeywordField(),
                    "value": fields.FloatField(),
                    "sensitive": fields.BooleanField(),
                }
            ),
            "datetime": fields.NestedField(
                properties={
                    "pn_id": fields.KeywordField(),
                    "pn_name": fields.KeywordField(),
                    "value": fields.DateField(),
                    "sensitive": fields.BooleanField(),
                }
            ),
            "schemas": fields.NestedField(
                properties={"schema_id": fields.KeywordField()}
            ),
        },
    )


def prepare_generic_parameters(instance, type):
    """Returns the parameters associated with the provided instance,
    formatted for elasticsearch."""

    type_dict = {
        "project": ProjectParameter,
        "experiment": ExperimentParameter,
        "dataset": DatasetParameter,
        "datafile": DatafileParameter,
    }
    OBJPARAMETERS = type_dict[type]

    paramsets = list(instance.getParameterSets())
    parameter_groups = {
        "string": [],
        "numerical": [],
        "datetime": [],
        "schemas": [],
    }
    for paramset in paramsets:
        param_type = {1: "datetime", 2: "string", 3: "numerical"}
        param_glob = OBJPARAMETERS.objects.filter(parameterset=paramset).values_list(
            "name",
            "datetime_value",
            "string_value",
            "numerical_value",
        )
        parameter_groups["schemas"].append({"schema_id": paramset.schema_id})
        for sublist in param_glob:
            PN = ParameterName.objects.get(id=sublist[0])
            param_dict = {}
            type_idx = 0
            for idx, value in enumerate(sublist[1:-1]):
                if value not in [None, ""]:
                    param_dict["pn_id"] = str(PN.id)
                    param_dict["pn_name"] = str(PN.full_name)
                    param_dict["sensitive"] = PN.sensitive
                    type_idx = idx + 1
                    if type_idx == 1:
                        param_dict["value"] = value
                    elif type_idx == 2:
                        param_dict["value"] = str(value)
                    elif type_idx == 3:
                        param_dict["value"] = float(value)
            if type_idx:
                parameter_groups[param_type[type_idx]].append(param_dict)
    return parameter_groups


@registry.register_document
class ExperimentDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(
            self, actions=actions, **elasticsearch_parallel_index_settings
        )

    class Index:
        name = "experiment"
        settings = elasticsearch_index_settings

    id = fields.KeywordField()
    title = fields.TextField(fields={"raw": fields.KeywordField()}, analyzer=analyzer)
    description = fields.TextField(
        fields={"raw": fields.KeywordField()}, analyzer=analyzer
    )
    projects = fields.NestedField(
        properties={
            "id": fields.KeywordField(),
            "name": fields.TextField(fields={"raw": fields.KeywordField()}),
        }
    )
    public_access = fields.IntegerField()
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    institution_name = fields.KeywordField()
    created_by = fields.ObjectField(properties={"username": fields.KeywordField()})
    acls = generic_acl_structure()
    parameters = generic_parameter_structure()
    tags = fields.TextField(attr="tags_for_indexing")

    def prepare_acls(self, instance):
        """Returns the ExperimentACLs associated with an
        experiment, formatted for elasticsearch.
        """
        return_list = []
        for acl in instance.experimentacl_set.select_related("user").exclude(
            user__id=settings.PUBLIC_USER_ID
        ):
            acl_dict = {}
            if acl.user is not None:
                acl_dict["pluginId"] = "django_user"
                acl_dict["entityId"] = acl.user.id
            if acl.group is not None:
                acl_dict["pluginId"] = "django_group"
                acl_dict["entityId"] = acl.group.id
            if acl.token is not None:
                continue  # token access shouldn't be added to search
            if acl_dict not in return_list:
                return_list.append(acl_dict)
        return return_list

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "experiment")

    class Django:
        model = Experiment
        related_models = [
            User,
            ExperimentACL,
            ExperimentParameterSet,
            ExperimentParameter,
            Schema,
            ParameterName,
        ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.experiment_set.all()
        if isinstance(related_instance, ExperimentACL):
            return related_instance.experiment
        if isinstance(related_instance, ExperimentParameterSet):
            return related_instance.experiment
        if isinstance(related_instance, ExperimentParameter):
            return related_instance.parameterset.experiment
        if isinstance(related_instance, Schema):
            return Experiment.objects.filter(
                experimentparameterset__schema=related_instance
            )
        if isinstance(related_instance, ParameterName):
            return Experiment.objects.filter(
                experimentparameterset__schema__parametername=related_instance
            )
        return None


@registry.register_document
class DatasetDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(
            self, actions=actions, **elasticsearch_parallel_index_settings
        )

    class Index:
        name = "dataset"
        settings = elasticsearch_index_settings

    id = fields.KeywordField()
    description = fields.TextField(
        fields={"raw": fields.KeywordField()}, analyzer=analyzer
    )
    experiments = fields.NestedField(
        properties={
            "id": fields.KeywordField(),
            "title": fields.TextField(fields={"raw": fields.KeywordField()}),
        }
    )
    instrument = fields.NestedField(
        properties={
            "id": fields.KeywordField(),
            "name": fields.TextField(
                fields={"raw": fields.KeywordField()},
            ),
        }
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()
    public_access = fields.IntegerField()
    acls = generic_acl_structure()
    parameters = generic_parameter_structure()
    tags = fields.TextField(attr="tags_for_indexing")

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.experiments.all().values_list("public_access", flat=True)
            return max(list(flags))
        return instance.public_access

    def prepare_acls(self, instance):
        """Returns the datasetACLs associated with this
        dataset, formatted for elasticsearch.
        """
        return_list = []
        if settings.ONLY_EXPERIMENT_ACLS:
            for exp in instance.experiments.all():
                for acl in exp.experimentacl_set.select_related("user").exclude(
                    user__id=settings.PUBLIC_USER_ID
                ):
                    acl_dict = {}
                    if acl.user is not None:
                        acl_dict["pluginId"] = "django_user"
                        acl_dict["entityId"] = acl.user.id
                    if acl.group is not None:
                        acl_dict["pluginId"] = "django_group"
                        acl_dict["entityId"] = acl.group.id
                    if acl.token is not None:
                        continue  # token access shouldn't be added to search
                    if acl_dict not in return_list:
                        return_list.append(acl_dict)
        else:
            for acl in instance.datasetacl_set.select_related("user").exclude(
                user__id=settings.PUBLIC_USER_ID
            ):
                acl_dict = {}
                if acl.user is not None:
                    acl_dict["pluginId"] = "django_user"
                    acl_dict["entityId"] = acl.user.id
                if acl.group is not None:
                    acl_dict["pluginId"] = "django_group"
                    acl_dict["entityId"] = acl.group.id
                if acl.token is not None:
                    continue  # token access shouldn't be added to search
                if acl_dict not in return_list:
                    return_list.append(acl_dict)
        return return_list

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "dataset")

    class Django:
        model = Dataset
        related_models = [
            Experiment,
            Instrument,
            DatasetParameterSet,
            DatasetParameter,
            Schema,
            ParameterName,
        ]
        if not settings.ONLY_EXPERIMENT_ACLS:
            related_models += [DatasetACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Experiment):
            return related_instance.datasets.all()
        if isinstance(related_instance, Instrument):
            return related_instance.dataset_set.all()
        if isinstance(related_instance, DatasetParameterSet):
            return related_instance.dataset
        if isinstance(related_instance, DatasetParameter):
            return related_instance.parameterset.dataset
        if isinstance(related_instance, Schema):
            return Dataset.objects.filter(datasetparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return Dataset.objects.filter(
                datasetparameterset__schema__parametername=related_instance
            )
        if not settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, DatasetACL):
                return related_instance.dataset
        return None


@registry.register_document
class DataFileDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(
            self, actions=actions, **elasticsearch_parallel_index_settings
        )

    class Index:
        name = "datafile"
        settings = elasticsearch_index_settings

    id = fields.KeywordField()
    filename = fields.TextField(
        fields={"raw": fields.KeywordField()}, analyzer=analyzer
    )
    file_extension = fields.KeywordField(attr="filename")
    created_time = fields.DateField()
    modification_time = fields.DateField()
    size = fields.LongField()
    verified = fields.BooleanField(attr="verified")
    dataset = fields.NestedField(
        properties={
            "id": fields.KeywordField(),
            "description": fields.TextField(fields={"raw": fields.KeywordField()}),
            "experiments": fields.NestedField(
                properties={
                    "id": fields.KeywordField(),
                }
            ),
        }
    )
    public_access = fields.IntegerField()
    acls = generic_acl_structure()
    parameters = generic_parameter_structure()
    tags = fields.TextField(attr="tags_for_indexing")

    def prepare_file_extension(self, instance):
        """
        Retrieve file extensions from filename - File extension taken as the
        entire string after first full stop.
        i.e. 'filename.tar.gz' has an extension of 'tar.gz'
        """
        try:
            extension = instance.filename.split(".", 1)[1]
        except (IndexError):
            extension = ""
        return extension

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.dataset.experiments.all().values_list(
                "public_access", flat=True
            )
            return max(list(flags))
        return instance.public_access

    def prepare_acls(self, instance):
        """Returns the datafileACLs associated with this
        datafile, formatted for elasticsearch.
        """
        return_list = []
        if settings.ONLY_EXPERIMENT_ACLS:
            for exp in instance.dataset.experiments.all():
                for acl in exp.experimentacl_set.select_related("user").exclude(
                    user__id=settings.PUBLIC_USER_ID
                ):
                    acl_dict = {}
                    if acl.user is not None:
                        acl_dict["pluginId"] = "django_user"
                        acl_dict["entityId"] = acl.user.id
                    if acl.group is not None:
                        acl_dict["pluginId"] = "django_group"
                        acl_dict["entityId"] = acl.group.id
                    if acl.token is not None:
                        continue  # token access shouldn't be added to search
                    if acl_dict not in return_list:
                        return_list.append(acl_dict)
        else:
            for acl in instance.datafileacl_set.select_related("user").exclude(
                user__id=settings.PUBLIC_USER_ID
            ):
                acl_dict = {}
                if acl.user is not None:
                    acl_dict["pluginId"] = "django_user"
                    acl_dict["entityId"] = acl.user.id
                if acl.group is not None:
                    acl_dict["pluginId"] = "django_group"
                    acl_dict["entityId"] = acl.group.id
                if acl.token is not None:
                    continue  # token access shouldn't be added to search
                if acl_dict not in return_list:
                    return_list.append(acl_dict)
        return return_list

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "datafile")

    class Django:
        model = DataFile
        related_models = [
            Dataset,
            Experiment,
            DatafileParameterSet,
            DatafileParameter,
            Schema,
            ParameterName,
            DataFileObject,
        ]
        queryset_pagination = 100000
        if not settings.ONLY_EXPERIMENT_ACLS:
            related_models += [DatafileACL]

    def get_queryset(self):
        return super().get_queryset().select_related("dataset")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.datafile_set.all()
        if isinstance(related_instance, Experiment):
            return DataFile.objects.filter(dataset__experiments=related_instance)
        if isinstance(related_instance, DatafileParameterSet):
            return related_instance.datafile
        if isinstance(related_instance, DatafileParameter):
            return related_instance.parameterset.datafile
        if isinstance(related_instance, Schema):
            return DataFile.objects.filter(
                datafileparameterset__schema=related_instance
            )
        if isinstance(related_instance, ParameterName):
            return DataFile.objects.filter(
                datafileparameterset__schema__parametername=related_instance
            )
        if isinstance(related_instance, DataFileObject):
            return related_instance.datafile
        if not settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, DatafileACL):
                return related_instance.datafile
        return None


@registry.register_document
class ProjectDocument(Document):
    class Index:
        name = "project"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    id = fields.KeywordField()
    name = fields.TextField(fields={"raw": fields.KeywordField()}, analyzer=analyzer)
    description = fields.TextField(
        fields={"raw": fields.KeywordField()}, analyzer=analyzer
    )
    start_time = fields.DateField()
    end_time = fields.DateField()
    institution = fields.NestedField(
        properties={
            "name": fields.TextField(
                fields={"raw": fields.KeywordField()},
            )
        }
    )
    principal_investigator = fields.NestedField(
        properties={
            "username": fields.TextField(fields={"raw": fields.KeywordField()}),
            "fullname": fields.TextField(fields={"raw": fields.KeywordField()}),
        }
    )
    public_access = fields.IntegerField()
    acls = generic_acl_structure()
    parameters = generic_parameter_structure()
    tags = fields.TextField(attr="tags_for_indexing")

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.experiments.all().values_list("public_access", flat=True)
            return max(list(flags))
        return instance.public_access

    def prepare_acls(self, instance):
        """Returns the ProjectACLs associated with this
        project, formatted for elasticsearch.
        """
        return_list = []
        if settings.ONLY_EXPERIMENT_ACLS:
            for exp in instance.experiments.all():
                for acl in exp.experimentacl_set.select_related("user").exclude(
                    user__id=settings.PUBLIC_USER_ID
                ):
                    acl_dict = {}
                    if acl.user is not None:
                        acl_dict["pluginId"] = "django_user"
                        acl_dict["entityId"] = acl.user.id
                    if acl.group is not None:
                        acl_dict["pluginId"] = "django_group"
                        acl_dict["entityId"] = acl.group.id
                    if acl.token is not None:
                        continue  # token access shouldn't be added to search
                    if acl_dict not in return_list:
                        return_list.append(acl_dict)
        else:
            for acl in instance.projectacl_set.select_related("user").exclude(
                user__id=settings.PUBLIC_USER_ID
            ):
                acl_dict = {}
                if acl.user is not None:
                    acl_dict["pluginId"] = "django_user"
                    acl_dict["entityId"] = acl.user.id
                if acl.group is not None:
                    acl_dict["pluginId"] = "django_group"
                    acl_dict["entityId"] = acl.group.id
                if acl.token is not None:
                    continue  # token access shouldn't be added to search
                if acl_dict not in return_list:
                    return_list.append(acl_dict)
        return return_list

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "project")

    def prepare_principal_investigator(self, instance):
        username = instance.principal_investigator.username
        fullname = " ".join(
            [
                instance.principal_investigator.first_name,
                instance.principal_investigator.last_name,
            ]
        )
        return dict({"username": username, "fullname": fullname})

    class Django:
        model = Project
        related_models = [
            User,
            ProjectParameterSet,
            ProjectParameter,
            Schema,
            ParameterName,
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            related_models += [Experiment]
        else:
            related_models += [ProjectACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.project_set.all()
        if isinstance(related_instance, ProjectParameterSet):
            return related_instance.project
        if isinstance(related_instance, ProjectParameter):
            return related_instance.parameterset.project
        if isinstance(related_instance, Schema):
            return Project.objects.filter(projectparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return Project.objects.filter(
                projectparameterset__schema__parametername=related_instance
            )
        if settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, Experiment):
                return related_instance.datasets.all()
        else:
            if isinstance(related_instance, ProjectACL):
                return related_instance.project
        return None
