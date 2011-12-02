import logging

from haystack.query import SearchQuerySet
from tardis.tardis_portal.forms import RawSearchForm
from haystack.views import SearchView

logger = logging.getLogger(__name__)


class ExperimentSearchView(SearchView):
    def __name__(self):
        return "ExperimentSearchView"
    
    def extra_context(self):
        extra = super(ExperimentSearchView, self).extra_context()
        # Results may contain Experiments, Datasets and Dataset_Files.
        # Group them into experiments, noting whether or not the search
        # hits were in the Dataset(s) or Dataset_File(s)
        results = self.results
        
        experiments = {}
        access_list = []

        if self.request.user.is_authenticated():
            access_list.extend([e.pk for e in authz.get_accessible_experiments(self.request)])

        access_list.extend([e.pk for e in Experiment.objects.filter(public=True)])

        for r in results:
            i = int(r.experiment_id_stored)

            if i not in access_list:
                continue

            if i not in experiments.keys():
                experiments[i]= {}
                experiments[i]['sr'] = r
                experiments[i]['dataset_hit'] = False
                experiments[i]['dataset_file_hit'] = False
                experiments[i]['experiment_hit'] =False

            if r.model == Experiment:
                experiments[i]['experiment_hit'] = True
            elif r.model == Dataset:
                experiments[i]['dataset_hit'] = True
            elif r.model == Dataset_File:
                experiments[i]['dataset_file_hit'] = True

        extra['experiments'] = experiments
        return extra

    # override SearchView's method in order to
    # return a ResponseContext
    def create_response(self):
        import re
        (paginator, page) = self.build_page()
       
        # Remove unnecessary whitespace and replace necessary whitespace with '+'
        # TODO this should just be done in the form clean...
        query = re.sub('\s*?:\s*', ':', self.query).replace(' ','+')
        query = SearchQueryString(query) 
        context = {
                'query': query,
                'form': self.form,
                'page': page,
                'paginator' : paginator,
                }
        context.update(self.extra_context())

        return render_response_index(self.request, self.template, context)
        #return render_to_response(self.template, context, context_instance=self.context_class(self.request))


@login_required
def single_search(request):
    sqs = SearchQuerySet()
    return ExperimentSearchView(
            template = 'search/search.html',
            searchqueryset=sqs,
            form_class=RawSearchForm,
            ).__call__(request)


