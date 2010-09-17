#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import template
from datetime import datetime
import time

register = template.Library()


@register.filter
def todatetime(value):
    return datetime(*time.localtime(time.mktime(value))[:6])
