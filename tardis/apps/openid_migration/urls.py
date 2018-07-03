from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^migrate-accounts/$', views.migrate_accounts),

]
