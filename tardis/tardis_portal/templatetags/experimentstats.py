#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import template
from tardis.tardis_portal.models import DataFile

register = template.Library()


@register.filter
def experiment_file_count(value):
    return DataFile.objects.filter(dataset__experiments__pk=value).count()

# @register.filter
# def experiment_file_size(value):....
#     return DataFile.objects.filter(dataset__experiment__pk=value).
#         aggregate(Sum('size'))['size__sum']
