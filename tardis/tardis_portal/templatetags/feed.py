#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from datetime import datetime

from django import template

register = template.Library()


@register.filter
def todatetime(value):
    return datetime(*time.localtime(time.mktime(value))[:6])
