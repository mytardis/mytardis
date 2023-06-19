from django.urls import include, re_path

urlpatterns = [
    re_path("", include("social_django.urls", namespace="social")),
]
