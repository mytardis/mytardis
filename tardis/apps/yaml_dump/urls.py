from django.urls import include, re_path
from tardis.apps.yaml_dump.views.idwyaml import IDWYAMLView

from rest_framework import routers

#router = routers.DefaultRouter()
#router.register(r'project-yaml', ProjectYAMLView,basename='project-yaml')
#yaml_urls = re_path(r"^", include(router.urls))
urlpatterns = [
    re_path('idw-yaml/', IDWYAMLView.as_view(), name='idw-yaml')
]