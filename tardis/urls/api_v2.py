from django.conf.urls import include, url
from rest_framework import routers
from tardis.tardis_portal.api_v2 import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'storageboxes', views.StorageBoxViewSet)
router.register(r'facilities', views.FacilityViewSet)
router.register(r'instruments', views.InstrumentViewSet)
router.register(r'experiments', views.ExperimentViewSet)
router.register(r'datasets', views.DatasetViewSet)
router.register(r'datafiles', views.DataFileViewSet)
router.register(r'datafileobjects', views.DataFileObjectViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
api_v2_urls = [
    url('', include(router.urls)),
    url('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
