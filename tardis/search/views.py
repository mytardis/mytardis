"""
views relevant to search
"""
import logging

from haystack.generic_views import SearchView

from tardis.search.forms import GroupedSearchForm

logger = logging.getLogger(__name__)


class SingleSearchView(SearchView):
    form_class = GroupedSearchForm
    template_name = 'search/search.html'

    def form_valid(self, form):
        sqs = form.search(user=self.request.user)
        context = self.get_context_data(**{
            self.form_name: form,
            'query': form.cleaned_data.get(self.search_field),
            'object_list': sqs,
        })
        return self.render_to_response(context)
