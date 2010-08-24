#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import template
from tardis.tardis_portal.models import *

register = template.Library()


@register.filter
def dsparametertypecheck(value, arg):
    datasetparameter = DatasetParameter.objects.get(id=arg)

    if datasetparameter.name.name.endswith('Image'):
        dsid = datasetparameter.dataset.id
        return "<img src='/displayDatasetImage/" + str(dsid) + '/' \
            + datasetparameter.name.name + "/' />"
    else:
        return value


@register.filter
def dfparametertypecheck(value, arg):
    datafileparameter = DatafileParameter.objects.get(id=arg)

    if datafileparameter.name.name.endswith('Image'):
        dfid = datafileparameter.dataset_file.id
        return "<img src='/displayDatafileImage/" + str(dfid) + '/' \
            + datafileparameter.name.name + "/' />"
    else:
        return value
