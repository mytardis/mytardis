"""
views relevant to search
"""
import logging

from django.views.generic.base import TemplateView

logger = logging.getLogger(__name__)


class SearchView(TemplateView):

    template_name = 'search.html'
