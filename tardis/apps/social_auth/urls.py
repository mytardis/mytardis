from django.conf.urls import include, url

urlpatterns = [
    url('', include('social_django.urls', namespace='social')),
]
