#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import template
from tardis.tardis_portal.models import *

register = template.Library()


@register.filter
def dsparametertypecheck(value, arg):
    datasetparameter = DatasetParameter.objects.get(id=arg)

    if datasetparameter.name.name.endswith('Image'):
        dsid = datasetparameter.parameterset.dataset.id
        psid = datasetparameter.parameterset.id
        return "<img src='/displayDatasetImage/" + str(dsid) + '/' \
            + str(psid) + '/' + datasetparameter.name.name + "/' />"
    else:
        return value


@register.filter
def dfparametertypecheck(value, arg):
    datafileparameter = DatafileParameter.objects.get(id=arg)

    if datafileparameter.name.name.endswith('Image'):
        dfid = datafileparameter.parameterset.dataset_file.id
        psid = datafileparameter.parameterset.id
        return "<img src='/displayDatafileImage/" + str(dfid) + '/' \
            + str(psid) + '/' + datafileparameter.name.name + "/' />"
    else:
        return value
