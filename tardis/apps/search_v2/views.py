"""
views relevant to search
"""
import logging
import datetime

from django.views.generic.base import TemplateView

from django_elasticsearch_dsl.search import Search

logger = logging.getLogger(__name__)


class SearchV2View(TemplateView):

    template_name = 'searchV2.html'

