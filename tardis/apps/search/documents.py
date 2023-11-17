import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, m2m_changed

from elasticsearch_dsl import analyzer, token_filter
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

# custom word_delimiter_graph filter to remove "split on numerics" behaviour
# i.e. XL500XA2 will no longer be split into XL,500,XA,2
word_delim_graph_custom = token_filter(
    "custom_word_delim_graph", type="word_delimiter_graph", split_on_numerics=False
)

analyzer = analyzer(
    "analyzer",
    tokenizer="standard",
    filter=["lowercase", "stop", word_delim_graph_custom],
)


def generic_acl_structure():
    """
    Return the ES structure of an ACL.

    - pluginId = type of ACL owner: user/group/token
    - entityId = ID of the owner
    """
    return fields.NestedField(
        properties={
            "pluginId": fields.KeywordField(),
            "entityId": fields.KeywordField(),
            "canDownload": fields.BooleanField(),
            "canSensitive": fields.BooleanField(),
        }
    )


def generic_parameter_structure():
    """
    Return the ES structure of object parameters and schema.
    The parameter structure splits out string/numerical/datetime
    parameters so that ES can specifically handle each of their
    datatypes.

    - Schemas:
      - schema_id: Id of the object schemas
    - string/numerical/datetime:
      - pn_id: Id of parameter name
      - pn_name: Name of parameter name
      - value: value of parameter
      - sensitive: whether parameter name is sensitive
    """
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


def prepare_generic_acls_build(INSTANCE_ACL_SET, return_list):
    """Returns the ACLs associated with this
    object, formatted for elasticsearch.
    """
    for acl in INSTANCE_ACL_SET:
        acl_dict = {}
        if acl["user__id"] is not None:
            acl_dict["pluginId"] = "django_user"
            acl_dict["entityId"] = acl["user__id"]
        if acl["group__id"] is not None:
            acl_dict["pluginId"] = "django_group"
            acl_dict["entityId"] = acl["group__id"]
        if acl["token__id"] is not None:
            # token access shouldn't be added to search
            # unless search is given a way of checking token expiry
            continue
        # add in permission booleans
        acl_dict["canDownload"] = acl["canDownload"]
        acl_dict["canSensitive"] = acl["canSensitive"]
        if acl_dict not in return_list:
            return_list.append(acl_dict)


def prepare_generic_acls(type, INSTANCE_ACL_SET, INSTANCE_EXPS=None):
    """Returns the ACLs associated with this
    object, formatted for elasticsearch.

    This function is mostly just a wrapper around "prepare_generic_acls_build"
    to account for current macro/micro behaviour.
    """
    return_list = []
    if settings.ONLY_EXPERIMENT_ACLS and type != "experiment":
        for exp in INSTANCE_EXPS.all():
            prepare_generic_acls_build(
                exp.experimentacl_set.select_related("user", "group", "token")
                .all()
                .exclude(user__id=settings.PUBLIC_USER_ID)
                .values(
                    "user__id",
                    "group__id",
                    "token__id",
                    "canDownload",
                    "canSensitive",
                ),
                return_list,
            )
    else:
        prepare_generic_acls_build(
            INSTANCE_ACL_SET.select_related("user", "group", "token")
            .all()
            .exclude(user__id=settings.PUBLIC_USER_ID)
            .values(
                "user__id",
                "group__id",
                "token__id",
                "canDownload",
                "canSensitive",
            ),
            return_list,
        )
    return return_list


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

    # get list of object parametersets
    paramsets = list(instance.getParameterSets())
    parameter_groups = {
        "string": [],
        "numerical": [],
        "datetime": [],
        "schemas": [],
    }
    # iterate over parametersets of an object
    for paramset in paramsets:
        param_type = {1: "datetime", 2: "string", 3: "numerical"}
        # query parameters from parameterset
        param_glob = OBJPARAMETERS.objects.filter(parameterset=paramset).values_list(
            "name",
            "datetime_value",
            "string_value",
            "numerical_value",
        )
        # add schema information to dict
        parameter_groups["schemas"].append({"schema_id": paramset.schema_id})
        # iterate over parameter info "name/datetime/string/numerical"
        for sublist in param_glob:
            # query parametername info using "name"
            PN = ParameterName.objects.get(id=sublist[0])
            # build dict for param
            param_dict = {}
            type_idx = 0
            # iterate over datetime/string/numerical info
            for idx, value in enumerate(sublist[1:]):
                # if datetime/string/numerical atually contains info
                if value not in [None, ""]:
                    # add parametername info to dict
                    param_dict["pn_id"] = str(PN.id)
                    param_dict["pn_name"] = str(PN.full_name)
                    param_dict["sensitive"] = PN.sensitive
                    type_idx = idx + 1
                    # detect type of param, and add value to dict
                    if type_idx == 1:
                        param_dict["value"] = value
                    elif type_idx == 2:
                        param_dict["value"] = str(value)
                    elif type_idx == 3:
                        param_dict["value"] = float(value)
            # if parameter with a value is added, add param_dict to
            # parameters_dict
            if type_idx:
                parameter_groups[param_type[type_idx]].append(param_dict)
    return parameter_groups


class MyTardisDocument(Document):
    """
    Generalised class for MyTardis objects
    """

    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(
            self, actions=actions, **elasticsearch_parallel_index_settings
        )

    id = fields.KeywordField()
    public_access = fields.IntegerField()
    acls = generic_acl_structure()
    parameters = generic_parameter_structure()
    tags = fields.TextField(attr="tags_for_indexing")


@registry.register_document
class ProjectDocument(MyTardisDocument):
    class Index:
        name = "project"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

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

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.experiments.all().values_list("public_access", flat=True)
            if list(flags):
                return max(list(flags))
            return 1
        return instance.public_access

    def prepare_acls(self, instance):
        return prepare_generic_acls(
            "project",
            instance.projectacl_set.all(),
            INSTANCE_EXPS=instance.experiments.all(),
        )

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
            ParameterName,
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            related_models += [Experiment, ExperimentACL]
        else:
            related_models += [ProjectACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.project_set.all()
        if isinstance(related_instance, ProjectParameterSet):
            return related_instance.project
        if isinstance(related_instance, ProjectParameter):
            return related_instance.parameterset.project
        if isinstance(related_instance, ParameterName):
            return Project.objects.filter(
                projectparameterset__schema__parametername=related_instance
            )
        if settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, Experiment):
                return related_instance.projects.all()
            if isinstance(related_instance, ExperimentACL):
                return related_instance.experiment.projects.all()
        else:
            if isinstance(related_instance, ProjectACL):
                return related_instance.project
        return None


@registry.register_document
class ExperimentDocument(MyTardisDocument):
    class Index:
        name = "experiment"
        settings = elasticsearch_index_settings

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
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    institution_name = fields.KeywordField()
    created_by = fields.ObjectField(properties={"username": fields.KeywordField()})

    def prepare_acls(self, instance):
        return prepare_generic_acls("experiment", instance.experimentacl_set.all())

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "experiment")

    class Django:
        model = Experiment
        related_models = [
            User,
            ExperimentACL,
            ExperimentParameterSet,
            ExperimentParameter,
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
        if isinstance(related_instance, ParameterName):
            return Experiment.objects.filter(
                experimentparameterset__schema__parametername=related_instance
            )
        return None


@registry.register_document
class DatasetDocument(MyTardisDocument):
    class Index:
        name = "dataset"
        settings = elasticsearch_index_settings

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

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.experiments.all().values_list("public_access", flat=True)
            if list(flags):
                return max(list(flags))
            return 1
        return instance.public_access

    def prepare_acls(self, instance):
        return prepare_generic_acls(
            "dataset",
            instance.datasetacl_set.all(),
            INSTANCE_EXPS=instance.experiments.all(),
        )

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "dataset")

    class Django:
        model = Dataset
        related_models = [
            Experiment,
            Instrument,
            DatasetParameterSet,
            DatasetParameter,
            ParameterName,
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            related_models += [ExperimentACL]
        else:
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
        if isinstance(related_instance, ParameterName):
            return Dataset.objects.filter(
                datasetparameterset__schema__parametername=related_instance
            )
        if settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, ExperimentACL):
                return related_instance.experiment.datasets.all()
        else:
            if isinstance(related_instance, DatasetACL):
                return related_instance.dataset
        return None


@registry.register_document
class DataFileDocument(MyTardisDocument):
    class Index:
        name = "datafile"
        settings = elasticsearch_index_settings

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

    def prepare_file_extension(self, instance):
        """
        Retrieve file extensions from filename - File extension taken as the
        string after last full stop.
        i.e. 'filename.tar.gz' has an extension of 'gz' not 'tar.gz'
        """
        try:
            split = instance.filename.split(".")
            if len(split) > 1:
                extension = split[-1]
            else:
                extension = ""
        except IndexError:
            extension = ""
        return extension

    def prepare_public_access(self, instance):
        if settings.ONLY_EXPERIMENT_ACLS:
            flags = instance.dataset.experiments.all().values_list(
                "public_access", flat=True
            )
            if list(flags):
                return max(list(flags))
            return 1
        return instance.public_access

    def prepare_acls(self, instance):
        return prepare_generic_acls(
            "datafile",
            instance.datafileacl_set.all(),
            INSTANCE_EXPS=instance.dataset.experiments.all(),
        )

    def prepare_parameters(self, instance):
        return prepare_generic_parameters(instance, "datafile")

    class Django:
        model = DataFile
        related_models = [
            Dataset,
            Experiment,
            DatafileParameterSet,
            DatafileParameter,
            ParameterName,
            DataFileObject,
        ]
        queryset_pagination = 100000

        if settings.ONLY_EXPERIMENT_ACLS:
            related_models += [ExperimentACL]
        else:
            related_models += [DatafileACL]

    # def get_queryset(self):
    #    return super().get_queryset().select_related("dataset")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.datafile_set.all()
        if isinstance(related_instance, Experiment):
            return DataFile.objects.filter(dataset__experiments=related_instance)
        if isinstance(related_instance, DatafileParameterSet):
            return related_instance.datafile
        if isinstance(related_instance, DatafileParameter):
            return related_instance.parameterset.datafile
        if isinstance(related_instance, ParameterName):
            return DataFile.objects.filter(
                datafileparameterset__schema__parametername=related_instance
            )
        if isinstance(related_instance, DataFileObject):
            return related_instance.datafile
        if settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(related_instance, ExperimentACL):
                # I'm not happy with the performance of having to query on dfs,
                # but this problem should get resolved when Macro+Micro ACL
                # functionality is combined?
                query = DataFile.objects.none()
                for dataset in related_instance.experiment.datasets.all():
                    query |= dataset.datafile_set.all()
                return query
        else:
            if isinstance(related_instance, DatafileACL):
                return related_instance.datafile
        return None


def update_es_after_removing_relation(instance, **kwargs):
    """
    This function and post_delete hooks are to handle deletions of instances
    triggering their relation re-indexing on PRE-delete rather than POST-delete
    in the django_elasticsearch_dsl package. This function simply re-indexes
    relevant documents a second time on post_delete.

    Probably clashes with the Async CelerySignalProcessor.
    """
    action = kwargs.pop("action", None)
    if isinstance(instance, ProjectACL):
        parent = instance.project
        doc = ProjectDocument()
        doc.update(parent)

    elif isinstance(instance, ExperimentACL):
        parent = instance.experiment
        doc = ExperimentDocument()
        doc.update(parent)
        if settings.ONLY_EXPERIMENT_ACLS:
            # also trigger other model rebuilds
            projects = instance.experiment.projects.all()
            datasets = instance.experiment.datasets.all()
            datafiles = DataFile.objects.none()
            for dataset in datasets:
                datafiles |= dataset.datafile_set.all()
            doc_proj = ProjectDocument()
            doc_set = DatasetDocument()
            doc_file = DataFileDocument()
            doc_proj.update(projects)
            doc_set.update(datasets)
            doc_file.update(datafiles)

    elif isinstance(instance, DatasetACL):
        parent = instance.dataset
        doc = DatasetDocument()
        doc.update(parent)

    elif isinstance(instance, DatafileACL):
        parent = instance.datafile
        doc = DataFileDocument()
        doc.update(parent)

    elif isinstance(instance, Experiment):
        print("Experiment triggered")
        if settings.ONLY_EXPERIMENT_ACLS:
            # also trigger other model rebuilds
            projects = instance.projects.all()
            doc_proj = ProjectDocument()
            doc_proj.update(projects)
        datasets = instance.datasets.all()
        datafiles = DataFile.objects.none()
        for dataset in datasets:
            datafiles |= dataset.datafile_set.all()
        doc_set = DatasetDocument()
        doc_file = DataFileDocument()
        doc_set.update(datasets)
        doc_file.update(datafiles)

    elif isinstance(instance, Dataset):
        print("dataset triggered")
        datafiles = instance.datafile_set.all()
        doc_file = DataFileDocument()
        doc_file.update(datafiles)


def setup_sync_signals():
    # Only enable post_delete signals if ELASTICSEARCH_DSL_AUTOSYNC=True
    if hasattr(settings, "ELASTICSEARCH_DSL_AUTOSYNC"):
        # check if ELASTICSEARCH_DSL_SIGNAL_PROCESSOR is set
        # and whether equal to CelerySignalProcessor
        check_for_celery_processor = False
        if hasattr(settings, "ELASTICSEARCH_DSL_SIGNAL_PROCESSOR"):
            if (
                settings.ELASTICSEARCH_DSL_SIGNAL_PROCESSOR
                == "django_elasticsearch_dsl.signals.CelerySignalProcessor"
            ):
                check_for_celery_processor = True

        # Only enable post_delete signals if AUTOSYNC=True and
        # ELASTICSEARCH_DSL_SIGNAL_PROCESSOR not set to CelerySignalProcessor
        if settings.ELASTICSEARCH_DSL_AUTOSYNC and not check_for_celery_processor:
            post_delete.connect(update_es_after_removing_relation, sender=ProjectACL)
            post_delete.connect(update_es_after_removing_relation, sender=ExperimentACL)
            post_delete.connect(update_es_after_removing_relation, sender=DatasetACL)
            post_delete.connect(update_es_after_removing_relation, sender=DatafileACL)
            post_delete.connect(update_es_after_removing_relation, sender=Experiment)
            post_delete.connect(update_es_after_removing_relation, sender=Dataset)


setup_sync_signals()
