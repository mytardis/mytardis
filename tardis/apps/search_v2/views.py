"""
views relevant to search
"""
import logging

from django.views.generic.base import TemplateView

from haystack.generic_views import SearchView
from elasticsearch import Elasticsearch
from django_elasticsearch_dsl.search import Search

from tardis.search.forms import GroupedSearchForm
from tardis.search.utils import SearchQueryString
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.hacks import oracle_dbops_hack
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import render_response_search, \
    render_response_index
from tardis.tardis_portal.views.utils import __forwardToSearchExperimentFormPage, \
    __getSearchExperimentForm, __processExperimentParameters


logger = logging.getLogger(__name__)


@oracle_dbops_hack
def search_experiment(request):

    """Either show the search experiment form or the result of the search
    experiment query.

    """

    if not request.GET:
        return __forwardToSearchExperimentFormPage(request)

    form = __getSearchExperimentForm(request)
    experiments = __processExperimentParameters(request, form)

    # check if the submitted form is valid
    if experiments is not None:
        bodyclass = 'list'
    else:
        return __forwardToSearchExperimentFormPage(request)

    results = []
    for e in experiments:
        result = {}
        result['sr'] = e
        result['dataset_hit'] = False
        result['experiment_hit'] = True
        results.append(result)
    c = {'header': 'Search Experiment',
         'experiments': results,
         'bodyclass': bodyclass}
    url = 'tardis_portal/search_experiment_results.html'
    return render_response_search(request, url, c)


def search_quick(request):
    get = False
    experiments = Experiment.objects.all().order_by('title')

    if 'results' in request.GET:
        get = True
        if 'quicksearch' in request.GET and request.GET['quicksearch']:
            experiments = \
                experiments.filter(
                    title__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    institution_name__icontains=request.GET['quicksearch']) | \
                experiments.filter(
                    experimentauthor__author__name__icontains=request.GET[
                        'quicksearch']) | \
                experiments.filter(
                    pdbid__pdbid__icontains=request.GET['quicksearch'])

            experiments = experiments.distinct()

            logger.debug(experiments)

    c = {'submitted': get, 'experiments': experiments,
         'subtitle': 'Search Experiments'}
    return render_response_index(
        request, 'tardis_portal/search_experiment.html', c)


class ExperimentSearchView(SearchView):
    def __name__(self):
        return "ExperimentSearchView"

    def extra_context(self):
        extra = super(ExperimentSearchView, self).extra_context()
        # Results may contain Experiments, Datasets and DataFiles.
        # Group them into experiments, noting whether or not the search
        # hits were in the Dataset(s) or DataFile(s)
        results = self.results
        facets = results.facet_counts()
        if facets:
            experiment_facets = facets['fields']['experiment_id_stored']
            experiment_ids = [int(f[0])
                              for f in experiment_facets if int(f[1]) > 0]
        else:
            experiment_ids = []

        access_list = []

        if self.request.user.is_authenticated:
            access_list.extend(
                [e.pk for e in
                 authz.get_accessible_experiments(self.request)])

        access_list.extend(
            [e.pk for e in Experiment.objects
                .exclude(public_access=Experiment.PUBLIC_ACCESS_NONE)
                .exclude(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)])

        ids = list(set(experiment_ids) & set(access_list))
        experiments = Experiment.objects.filter(pk__in=ids)\
                                        .order_by('-update_time')

        results = []
        for e in experiments:
            result = {'sr': e, 'dataset_hit': False,
                      'experiment_hit': False}
            results.append(result)

        extra['experiments'] = results
        return extra

    # override SearchView's method in order to
    # return a ResponseContext
    def create_response(self):
        (paginator, page) = self.build_page()

        # Remove unnecessary whitespace
        # TODO this should just be done in the form clean...
        query = SearchQueryString(self.query)
        context = {
            'search_query': query,
            'form': self.form,
            'page': page,
            'paginator': paginator,
        }
        context.update(self.extra_context())

        return render_response_index(self.request, self.template, context)


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


class SearchV2View(TemplateView):

    template_name = 'searchV2.html'

    def get_context_data(self, **kwargs):
        c = super(SearchV2View, self).get_context_data(**kwargs)
        query_text = self.request.GET.dict().get('q', '')
        client = Elasticsearch()
        s = Search(using=client)
        search = s.query(
            "multi_match",
            query=query_text,
            fields=["title", "description", "filename"]
        )
        results = search.execute()
        c['results'] = results
        c['hits'] = results.hits
        return c
