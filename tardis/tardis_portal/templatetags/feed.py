#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import time
from django import template

register = template.Library()


@register.filter
def todatetime(value):
    return datetime(*time.localtime(time.mktime(value))[:6])
