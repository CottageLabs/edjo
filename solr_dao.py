import solr, operator
from datetime import datetime, timedelta
from dao import DAO, ResultManager
from copy import deepcopy

class SolrDAO(DAO):
    
    def __init__(self, config):
        self.config = config
        self.solr = solr.Solr(self.config.solr_url)
        self.select = solr.SearchHandler(self.solr, self.config.solr_request_handler, arg_separator="__")

    def record(self, id):
        args = {"q" : {self.config.unique_id_field : [id]}}
        results = self._do_query(args)
        print results.results.results
        return results.results.results[0]

    def search(self, args):
        return self._do_query(args)
        
    def initial(self, args):
        args = deepcopy(args)
        if self.config.solr_text_search_field not in args["q"].keys():
            args["q"]["*"] = "*"
        args["rows"] = 0
        return self._do_query(args)
        
    def _do_query(self, args, arg_separator="__"):
        # we build all our solr args in one dictionary for convenience
        solr_args = {}
        solr_args['facet'] = "on"
        
        # Except the fields required explicitly by the solrpy api:
        
        #def __call__(self, q=None, fields=None, highlight=None,
        #         score=True, sort=None, sort_order="asc", **params):
        
        # do q separately
        
        # first do the actual 'q' arg
        qs = []
        for field in args['q'].keys():
            if self.config.is_field_facet(field):
                for value in args['q'][field]:
                    qs.append(field + ":\"" + value + "\"")
            elif self.config.is_range_facet(field):
                facet = self.config.get_facet(field)
                limit = args['q'][field][1]
                if limit == -1:
                    limit = facet.infinity
                qs.append(field + ":[" + str(args["q"][field][0]) + " TO " + str(limit) + "]")
            elif self.config.is_date_facet(field):
                facet = self.config.get_facet(field)
                limit = args['q'][field][1]
                if limit == -1:
                    now = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
                    limit = facet.infinity if facet.infinity is not None else now
                qs.append(field + ":[" + str(args["q"][field][0]) + " TO " + str(limit) + "]")
            elif self.config.is_query_facet(field):
                pass
            elif field == "*":
                for value in args['q'][field]:
                    qs.append(field + ":" + value)
            else:
                for value in args['q'][field]:
                    qs.append(field + ":" + value)
        
        # now there's an optional "search" part which should be appended to the q
        if args.has_key("search"):
            search = args['search']
            # if we detect a ":" in the search, we take it to be a lucene search
            if ":" in search:
                qs.append(search)
            else:
                # break the search by space and OR everything together
                clauses = []
                for term in search.split(" "):
                    clauses.append(self.config.solr_text_search_field + ":" + term)
                ors = " OR ".join(clauses)
                if ors != "":
                    qs.append("(" + ors + ")")
        
        q = " AND ".join(qs)
        
        if q == "": 
            q = "*:*"
        
        # start position (for paging)
        if args.has_key("start"):
            solr_args["start"] = args["start"]
        
        # set up the ranged search parameters
        if args.has_key("facet_range"):
            for facet_name in args["facet_range"]:
                facet = self.config.get_facet(facet_name)
                if solr_args.has_key("facet.range"):
                    solr_args["facet.range"].append(facet.field)
                else:
                    solr_args["facet.range"] = [facet.field]
                
                solr_args["f." + facet.field + ".facet.mincount"] = facet.mincount
                solr_args["f." + facet.field + ".facet.range.start"] = facet.min    
                solr_args["f." + facet.field + ".facet.range.end"] = facet.max    
                solr_args["f." + facet.field + ".facet.range.gap"] = facet.gap
        
        # set up the date range parameters
        if args.has_key("facet_date"):
            for facet_name in args["facet_date"]:
                facet = self.config.get_facet(facet_name)
                if solr_args.has_key("facet.date"):
                    solr_args["facet.date"].append(facet.field)
                else:
                    solr_args["facet.date"] = [facet.field]
                
                solr_args["f." + facet.field + ".facet.mincount"] = facet.mincount
                solr_args["f." + facet.field + ".facet.date.start"] = facet.min
                    
                if facet.max is not None:
                    solr_args["f." + facet.field + ".facet.date.end"] = facet.max
                else:
                    solr_args["f." + facet.field + ".facet.date.end"] = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
                    
                solr_args["f." + facet.field + ".facet.date.gap"] = facet.gap
        
        # set up the facet queries
        if args.has_key('facet_query'):
            for facet_name in args['facet_query']:
                facet = self.config.get_facet(facet_name)
                if not solr_args.has_key("facet.query"):
                    solr_args["facet.query"] = []
                for q in facet.queries:
                    solr_args["facet.query"].append(facet.field + ":" + q['query'])
        
        # facet mincount from config
        solr_args["facet.mincount"] = self.config.facet_mincount
        
        # number of rows to return
        if args.has_key("rows"):
            solr_args["rows"] = args["rows"]
            
        # plain facet fields
        if args.has_key("facet_field"):
            solr_args["facet.field"] = args["facet_field"]
        
        # sort options
        if args.has_key("sort"):
            sort_parts = []
            for sort_field, direction in args['sort']:
                sort_parts.append(sort_field + " " + direction)
            solr_args["sort"] = ", ".join(sort_parts)
        
        # solrpy convert the keywordargs
        solrpy_args = self.solrpyise(solr_args, arg_separator)
        
        results = self.select(q=q, **solrpy_args)
        return SolrResultManager(results, self.config, args)
    
    def solrpyise(self, dict, arg_separator="__"):
        edict = {}
        for key in dict.keys():
            ekey = self.esc(key, arg_separator)
            edict[str(ekey)] = dict[key]
        return edict
    
    def esc(self, solr_field, arg_separator="__"):
        return solr_field.replace(".", arg_separator)

class SolrResultManager(ResultManager):
    def __init__(self, results, config, args):
        ResultManager.__init__(self, results, config, args)

    def current_sort_order(self):
        return ResultManager.current_sort_order(self)
    
    def current_sort_fields(self):
        return ResultManager.current_sort_fields(self)

    def get_ordered_facets(self, facet_name):
        if self.config.is_field_facet(facet_name):
            return self._sort_facets_by_count(self.results.facet_counts['facet_fields'][facet_name])
        elif self.config.is_range_facet(facet_name):
            dict = self._get_range_dict(facet_name)
            return self._sort_facets_by_range(dict)
        elif self.config.is_date_facet(facet_name):
            dict = self._get_date_dict(facet_name)
            return self._sort_facets_by_range(dict)
        elif self.config.is_query_facet(facet_name):
            pass
    
    def in_args(self, facet, value=None):
        return ResultManager.in_args(self, facet, value)
            
    def get_search_constraints(self):
        return ResultManager.get_search_constraints(self)
            
    def get_range_values(self, facet_name):
        return ResultManager.get_range_values(self, facet_name)
    
    def has_values(self, facet_name):
        if self.config.is_field_facet(facet_name):
            return len(self.results.facet_counts['facet_fields'][facet_name]) > 0
        elif self.config.is_range_facet(facet_name):
            return len(self.results.facet_counts['facet_ranges'][facet_name]["counts"]) > 0
        elif self.config.is_date_facet(facet_name):
            return len(self.results.facet_counts['facet_dates'][facet_name]) > 0
        elif self.config.is_query_facet(facet_name):
            pass
        return False
    
    def is_start(self):
        return self.results.start == 0
        
    def is_end(self):
        return self.results.start + self.args['rows'] >= self.results.numFound
    
    def start(self):
        return self.results.start
        
    def finish(self):
        return self.results.start + self.set_size()
        
    def start_offset(self, off):
        return self.results.start + off
        
    def set_size(self):
        return len(self.results.results)
        
    def numFound(self):
        return self.results.numFound
        
    def set(self):
        return self.results.results
    
    def page_size(self):
        return ResultManager.page_size(self)
    
    def get_str(self, result, field):
        return ResultManager.get_str(self, result, field)
    
    def first_page_end(self):
        return ResultManager.first_page_end(self)
    
    def last_page_start(self):
        return self.results.numFound - (self.results.numFound % self.args['rows'])
        
    def get_previous(self, num):
        pairs = []
        for i in range(num + 1, 0, -1):
            first = self.results.start - (self.args['rows'] * i)
            if first >= self.args['rows']: # i.e. greater than the first page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def get_next(self, num):
        pairs = []
        for i in range(1, num + 1):
            first = self.results.start + (self.args['rows'] * i)
            last_page_size = self.results.numFound % self.args['rows']
            if first + self.args['rows'] <= self.results.numFound - last_page_size: # i.e. less than the last page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def _get_range_dict(self, facet):
        dict = self.results.facet_counts['facet_ranges'][facet]["counts"]
        keys = [int(key) for key in dict.keys()]
        keys.sort()
        rdict = {}
        for i in range(len(keys)):
            lower = int(keys[i])
            upper = -1
            if i < len(keys) - 1:
                upper = int(keys[i+1] - 1)
            r = (lower, upper)
            rdict[r] = dict[str(lower)]
        return rdict
        
    def _get_date_dict(self, facet):
        dict = self.results.facet_counts['facet_dates'][facet]
        keys = [(datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ"), d) for d in dict.keys() if d[0:2].isdigit()]
        keys = sorted(keys, key=operator.itemgetter(0))
        rdict = {}
        for i in range(len(keys)):
            lower, sl = keys[i]
            upper = -1
            if i < len(keys) - 1:
                upper, su = keys[i+1]
                upper = upper - timedelta(seconds=1)
            r = (lower, upper)
            rdict[r] = dict[sl]
        return rdict
    
    def _sort_facets_by_count(self, dict):
        return ResultManager._sort_facets_by_count(self, dict)
        
    def _sort_facets_by_range(self, dict):
        return ResultManager._sort_facets_by_range(self, dict)