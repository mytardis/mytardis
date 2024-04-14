from django.http import HttpResponse

import yaml
from rest_framework import generics
from rest_framework.authentication import RemoteUserAuthentication
from rest_framework.permissions import IsAuthenticated

from tardis.apps.projects.models import Project
from tardis.tardis_portal.api.serializers.project import ProjectSerializer


class ProjectView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    authentication_classes = [RemoteUserAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        return Project.safe.all(user=self.request.user)

    def get(self, request, *args, **kwargs):
        projects = Project.safe.all(user=request.user)
        serializer = ProjectSerializer(projects, many=True)
        response = super().get(request, *args, **kwargs)

        # Convert response data to YAML
        data = yaml.dump(response.data)

        # Create a YAML file
        response = HttpResponse(data, content_type="application/yaml")
        response["Content-Disposition"] = 'attachment; filename="data.yaml"'
        return response
