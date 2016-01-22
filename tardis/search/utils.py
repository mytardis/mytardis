class SearchQueryString(object):
    """
    Class to manage switching between space separated search queries and
    '+' separated search queries (for addition to urls

    TODO This would probably be better handled with filters
    """

    def __init__(self, query_string):
        import re
        # remove extra spaces around colons
        stripped_query = re.sub('\s*?:\s*', ':', query_string)

        # create a list of terms which can be easily joined by
        # spaces or pluses
        self.query_terms = stripped_query.split()

    def __unicode__(self):
        return ' '.join(self.query_terms)

    def url_safe_query(self):
        return '+'.join(self.query_terms)

    def query_string(self):
        return self.__unicode__()
