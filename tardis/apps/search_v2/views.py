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

    def get_context_data(self, **kwargs):
        c = super(SearchV2View, self).get_context_data(**kwargs)
        query_text = self.request.GET.dict().get('q', '')
        query_date_gt = self.request.GET.dict().get('dt_start', datetime.datetime(1970, 01, 01).strftime('%d%m%Y'))
        query_date_lt = self.request.GET.dict().get('dt_end', datetime.datetime.today().strftime('%d%m%Y'))
        s = Search()
        search = s.query(
            "multi_match",
            query=query_text,
            fields=["title", "description", "filename"]
        ).filter('range', created_time={'gte': query_date_gt, 'lte': query_date_lt, 'format': 'ddMMyyyy||yyyy'})
        results = search.execute()
        c['results'] = results
        c['hits'] = results.hits
        return c
