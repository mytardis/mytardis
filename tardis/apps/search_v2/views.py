"""
views relevant to search
"""
import logging

from django.views.generic.base import TemplateView


logger = logging.getLogger(__name__)


class SearchV2View(TemplateView):

    template_name = 'searchV2.html'
