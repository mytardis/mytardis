import logging

from django.http import HttpResponse

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from tardis.apps.projects.models import Project
from tardis.apps.yaml_dump.models.ingestion_metadata import IngestionMetadata
from tardis.apps.yaml_dump.utils.project import wrangle_project_into_IDW_YAML
from tardis.tardis_portal.api_v2.serializers.project import ProjectSerializer

logger = logging.getLogger("__name__")


class IDWYAMLView(generics.ListAPIView):
    # serializer_class = ProjectSerializer
    # authentication_classes = [RemoteUserAuthentication]
    permission_classes = [IsAuthenticated]
    project_serialiser_class = ProjectSerializer
    experiment_serialiser_class = ProjectSerializer

    # def get_serializer_context(self):
    #    context = super().get_serializer_context()
    #    context["request"] = self.request
    #    return context

    # def get_queryset(self):
    #    return Project.safe.all(user=self.request.user)

    def get(self, request, *args, **kwargs):
        ingestion_metadata = IngestionMetadata()
        logger.debug(request.user)
        project_queryset = Project.safe.all(user=request.user)
        # experiment_queryset = Project.safe.all(user=request.user)

        project_serialiser = self.project_serialiser_class(
            project_queryset, context={"request": request}, many=True
        )
        # experiment_serialiser = self.experiment_serialiser_class(experiment_queryset, context={'request': request}, many=True)

        response_results = {
            "projects": project_serialiser.data,
            # "experiments": experiment_serialiser.data,
        }

        logger.debug(response_results)
        processed = [
            wrangle_project_into_IDW_YAML(project)
            for project in response_results["projects"]
        ]
        logger.debug(processed)
        ingestion_metadata.projects = processed
        # response = Response(response_results)

        # Convert response data to YAML
        data = ingestion_metadata._to_yaml()

        # Create a YAML file
        response = HttpResponse(data, content_type="application/yaml")
        response["Content-Disposition"] = 'attachment; filename="data.yaml"'
        return response

    # def wrangle_projects(self, projects):
    #    for project in projects:
