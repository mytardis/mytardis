import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from elasticsearch_dsl import analysis, analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from tardis.tardis_portal.models import Project, Dataset, Experiment, \
    DataFile, Instrument, ObjectACL, ParameterName, Schema, ProjectParameter, \
    ExperimentParameter, DatasetParameter, DatafileParameter, \
    ProjectParameterSet, ExperimentParameterSet, DatasetParameterSet, \
    DatafileParameterSet

from tardis.tardis_portal.tests import suspendingreceiver

logger = logging.getLogger(__name__)


trigram = analysis.tokenizer('trigram', 'nGram', min_gram=3, max_gram=3)

analyzer = analyzer(
    "analyzer",
    tokenizer=trigram,
    filter='lowercase',
)


@registry.register_document
class ProjectDocument(Document):
    class Index:
        name = 'project'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    name = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    #public_access = fields.IntegerField()
    start_date = fields.DateField()
    end_date = fields.DateField()
    institution = fields.NestedField(properties={
        'name': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })
    lead_researcher = fields.NestedField(properties={
        'username': fields.StringField(
            fields={'raw': fields.KeywordField()}),
        'fullname': fields.StringField(
            fields={'raw': fields.KeywordField()})
    })
    objectacls = fields.ObjectField(properties={
        'pluginId': fields.KeywordField(),
        'entityId': fields.KeywordField()
    })
    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        }),
        'schemas' : fields.NestedField(properties = {
            'schema_id': fields.KeywordField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    def prepare_lead_researcher(self, instance):
        username = instance.lead_researcher.username
        fullname = " ".join([instance.lead_researcher.first_name,
                             instance.lead_researcher.last_name])
        return dict({"username":username, "fullname":fullname})

    class Django:
        model = Project
        related_models = [User, ObjectACL, Schema, ParameterName,
                          ProjectParameter, ProjectParameterSet]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.project_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_object.get_ct().model == "project":
                return related_instance.content_object
        if isinstance(related_instance, ProjectParameterSet):
            return related_instance.project
        if isinstance(related_instance, ProjectParameter):
            return related_instance.parameterset.project
        if isinstance(related_instance, Schema):
            return Project.objects.filter(projectparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return Project.objects.filter(projectparameterset__schema__parametername=related_instance)
        return None


@registry.register_document
class ExperimentDocument(Document):
    class Index:
        name = 'experiment'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    title = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    #public_access = fields.IntegerField()
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    #institution_name = fields.StringField()
    created_by = fields.ObjectField(properties={
        'username': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })
    project = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name' : fields.TextField(fields={'raw': fields.KeywordField()},
                                  analyzer=analyzer)
        })
    objectacls = fields.ObjectField(properties={
        'pluginId': fields.KeywordField(),
        'entityId': fields.KeywordField()
    })
    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        }),
        'schemas' : fields.NestedField(properties = {
            'schema_id': fields.KeywordField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = Experiment
        related_models = [Project, User, ObjectACL, Schema, ParameterName,
                          ExperimentParameter, ExperimentParameterSet]
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Project):
            return related_instance.experiment_set.all()
        if isinstance(related_instance, User):
            return related_instance.experiment_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_object.get_ct().model == "experiment":
                return related_instance.content_object
        if isinstance(related_instance, ExperimentParameterSet):
            return related_instance.experiment
        if isinstance(related_instance, ExperimentParameter):
            return related_instance.parameterset.experiment
        if isinstance(related_instance, Schema):
            return Experiment.objects.filter(experimentparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return Experiment.objects.filter(experimentparameterset__schema__parametername=related_instance)
        return None


@registry.register_document
class DatasetDocument(Document):
    class Index:
        name = 'dataset'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    experiments = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'title': fields.StringField(
            fields={'raw': fields.KeywordField()}
        ),
        'project': fields.NestedField(properties={
            'id': fields.KeywordField()
        })
    })
    objectacls = fields.ObjectField(properties={
            'pluginId': fields.KeywordField(),
            'entityId': fields.KeywordField()
        })
    instrument = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )}
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()
    tags = fields.StringField(attr='tags_for_indexing')

    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        }),
        'schemas' : fields.NestedField(properties = {
            'schema_id': fields.KeywordField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = Dataset
        related_models = [Project, Experiment, Instrument, ObjectACL,
                          Schema, ParameterName, DatasetParameter,
                          DatasetParameterSet]
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Project):
            return Dataset.objects.filter(experiments__project=related_instance)
        if isinstance(related_instance, Experiment):
            return related_instance.datasets.all()
        if isinstance(related_instance, Instrument):
            return related_instance.dataset_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_object.get_ct().model == "dataset":
                return related_instance.content_object
        if isinstance(related_instance, DatasetParameterSet):
            return related_instance.dataset
        if isinstance(related_instance, DatasetParameter):
            return related_instance.parameterset.dataset
        if isinstance(related_instance, Schema):
            return Dataset.objects.filter(datasetparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return Dataset.objects.filter(datasetparameterset__schema__parametername=related_instance)
        return None


@registry.register_document
class DataFileDocument(Document):
    class Index:
        name = 'datafile'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}
    id = fields.KeywordField()
    filename = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    file_extension = fields.KeywordField(attr='filename')
    created_time = fields.DateField()
    modification_time = fields.DateField()
    dataset = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'description': fields.StringField(
            fields={'raw': fields.KeywordField()}
        ),
        'experiments': fields.NestedField(properties={
            'id': fields.KeywordField(),
            'project':fields.NestedField(properties={
                'id': fields.KeywordField()
            }),
        }),
    })
    objectacls = fields.ObjectField(properties={
            'pluginId': fields.KeywordField(),
            'entityId': fields.KeywordField()
        })

    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'pn_name': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        }),
        'schemas' : fields.NestedField(properties = {
            'schema_id': fields.KeywordField()
        })
    })


    def prepare_file_extension(self, instance):
        """
        Retrieve file extensions from filename - File extension taken as entire
        string after first full stop.

        i.e. 'filename.tar.gz' has an extension of 'tar.gz'
        """
        try:
            extension = instance.filename.split('.',1)[1]
        except(IndexError):
            extension = ''
        return extension

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = DataFile
        related_models = [Dataset, Experiment, Project, ObjectACL,
                          Schema, ParameterName, DatafileParameter,
                          DatafileParameterSet]
        queryset_pagination = 100000

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.datafile_set.all()
        if isinstance(related_instance, Experiment):
            return DataFile.objects.filter(dataset__experiments=related_instance)
        if isinstance(related_instance, Project):
            return DataFile.objects.filter(dataset__experiments__project=related_instance)
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_object.get_ct().model == 'data file':
                return related_instance.content_object
        if isinstance(related_instance, DatafileParameterSet):
            return related_instance.datafile
        if isinstance(related_instance, DatafileParameter):
            return related_instance.parameterset.datafile
        if isinstance(related_instance, Schema):
            return DataFile.objects.filter(datafileparameterset__schema=related_instance)
        if isinstance(related_instance, ParameterName):
            return DataFile.objects.filter(datafileparameterset__schema__parametername=related_instance)
        return None

@suspendingreceiver(post_save, sender=Project)
@suspendingreceiver(post_save, sender=Experiment)
@suspendingreceiver(post_save, sender=Dataset)
@suspendingreceiver(post_save, sender=DataFile)
def update_search(instance, **kwargs):
    if isinstance(instance, Project):
        instance.to_search().save()
    if isinstance(instance, Experiment):
        instance.to_search().save()
    if isinstance(instance, Dataset):
        instance.to_search().save()
    if isinstance(instance, DataFile):
        instance.to_search().save()
