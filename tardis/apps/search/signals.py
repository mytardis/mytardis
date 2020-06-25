# encoding: utf-8
"""

Based on:

https://raw.githubusercontent.com/django-es/django-elasticsearch-dsl/master/django_elasticsearch_dsl/signals.py
https://github.com/django-es/django-elasticsearch-dsl/pull/87

"""

from __future__ import absolute_import

from django.apps import apps
from django.db import models

from django_elasticsearch_dsl.registries import registry

from tardis.celery import tardis_app

class BaseSignalProcessor(object):

    def __init__(self, connections):
        self.connections = connections
        self.setup()

    def setup(self):
        # Do nothing.
        pass

    def teardown(self):
        # Do nothing.
        pass

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in ('post_add', 'post_remove', 'post_clear'):
            self.handle_save(sender, instance)
        elif action in ('pre_remove', 'pre_clear'):
            self.handle_pre_delete(sender, instance)

    def handle_save(self, sender, instance, **kwargs):
        pk = instance.pk
        model = instance._meta.concrete_model
        model_name = model.__name__
        app_label = instance._meta.app_label

        if model in registry._models:
            print("registry_update")
            self.registry_update.delay(pk, app_label, model_name)

        if model in registry._related_models:
            print("registry_update_related")
            self.registry_update_related.delay(pk, app_label, model_name)

    def handle_pre_delete(self, sender, instance, **kwargs):
        registry.delete_related(instance)

    def handle_delete(self, sender, instance, **kwargs):
        registry.delete(instance, raise_on_error=False)

    @tardis_app.task(name="tardis_portal.es_dsl.registry_update", bind=True, ignore_result=True)
    def registry_update(self, pk, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            pass
        else:
            try:
                registry.update(
                    model.objects.get(pk=pk)
                )
            except Exception as e:
                self.retry(
                    countdown=60 * 10,
                    exc=e,
                    max_retries=6
                )

    @tardis_app.task(name="tardis_portal.es_dsl.registry_update_related", bind=True, ignore_result=True)
    def registry_update_related(self, pk, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            pass
        else:
            try:
                registry.update_related(
                    model.objects.get(pk=pk)
                )
            except Exception as e:
                self.retry(
                    countdown=60 * 10,
                    exc=e,
                    max_retries=6
                )


class CelerySignalProcessor(BaseSignalProcessor):

    def setup(self):
        # Listen to all model saves.
        models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)

        # Use to manage related objects update
        models.signals.m2m_changed.connect(self.handle_m2m_changed)
        models.signals.pre_delete.connect(self.handle_pre_delete)

    def teardown(self):
        # Listen to all model saves.
        models.signals.post_save.disconnect(self.handle_save)
        models.signals.post_delete.disconnect(self.handle_delete)
        models.signals.m2m_changed.disconnect(self.handle_m2m_changed)
        models.signals.pre_delete.disconnect(self.handle_pre_delete)
