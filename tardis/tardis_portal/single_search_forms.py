from haystack.forms import SearchForm

class RawSearchForm(SearchForm):
    
    def search(self):
        #self.clean()
        sqs = self.searchqueryset.raw_search(self.cleaned_data['q'])

        if self.load_all:
            sqs.load_all()

        return sqs
