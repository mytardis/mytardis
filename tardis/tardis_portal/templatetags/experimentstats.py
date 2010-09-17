#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import template
from tardis.tardis_portal.models import Dataset_File
from django.db.models import Sum

register = template.Library()


@register.filter
def experiment_file_count(value):
    return Dataset_File.objects.filter(dataset__experiment__pk=value).count()

# @register.filter
# def experiment_file_size(value):....
#     return Dataset_File.objects.filter(dataset__experiment__pk=value).
#         aggregate(Sum('size'))['size__sum']
