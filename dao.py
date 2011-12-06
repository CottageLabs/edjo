import operator

"""
args =
{
    # search query parameters
    # all query parameters are ANDed together (in Solr impl)
    "q" : {
        "range" : [lower, upper],
        "field" : [value1, value2, value3, ...],
        "date" : [lower, upper], 
        "query" : [query1, query2, query3, ...] # not implemented
    },
    "search" : "free text",
    
    # paging/result set information
    "start" : 0, # start position
    "rows" : 10, # total result set size to return
    "sort" : [["field", "asc|desc"], ...]
    
    # all of these are field names as specified in the configuration
    # for facets.  The remaining details for these are acquired from
    # the facet configuration (e.g. min, max, for ranges)
    "facet_field" : ["field1", "field2", ...],
    "facet_range" : ["field1", "field2", ...],
    "facet_date" : ["field1", "field2", ...],
    "facet_query" : ["field1", "field2", ...]
}
"""

class DAO(object):
    def __init__(self, config): pass
    def initial(self, args): pass
    def search(self, args): pass
    def record(self, id): pass
    
class ResultManager(object):
    def __init__(self, results, config, args):
        self.results = results
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()

    def current_sort_order(self):
        if not self.args.has_key('sort'):
            return []
        return self.args['sort']
    
    def current_sort_fields(self):
        if not self.args.has_key('sort'):
            return []
        return [k for k, v in self.args['sort']]

    def get_ordered_facets(self, facet_name): pass
    
    def in_args(self, facet_name, value=None):
        if value is not None:
            return self.args['q'].has_key(facet_name) and value in self.args['q'][facet_name]
        else:
            return self.args['q'].has_key(facet_name)
            
    def get_search_constraints(self):
        return self.args['q']
    
    def get_range_values(self, facet_name):
        lower = self.args["q"][facet_name][0]
        upper = self.args["q"][facet_name][1]
        return lower, upper
    
    def has_values(self, facet_name): pass
    
    def is_start(self): pass
        
    def is_end(self): pass
    
    def start(self): pass
        
    def finish(self): pass
        
    def start_offset(self, off): pass
        
    def set_size(self): pass
        
    def numFound(self): pass
        
    def set(self): pass
    
    def page_size(self):
        return self.args['rows']
    
    def get_str(self, result, field):
        field_obj = self.config.get_field(field)
        if field_obj is None:
            return ""
        return field_obj.get_value(self.args, result)
    
    def first_page_end(self):
        return self.args['rows']
    
    def last_page_start(self): pass
        
    def get_previous(self, num): pass
        
    def get_next(self, num): pass
    
    def _sort_facets_by_count(self, dict):
        return sorted(dict.iteritems(), key=operator.itemgetter(1), reverse=True)
        
    def _sort_facets_by_range(self, dict):
        # dict = {(a, b) : c, ....} ; we want to sort by a
        # first, cast the dict to tuples
        tups = [(a, b, dict[(a, b)]) for a, b in dict.keys()]
        return sorted(tups, key=operator.itemgetter(0))