from dao import DAO, ResultManager

import httplib
import uuid
import operator
import json

# TODO: no range / date support for ES dao yet.

class ElasticSearchDAO(DAO):

    def __init__(self, config):
        self.config = config

    def initial(self,args):
        return self.search(args)

    def search(self,args):
        return self._do_query(args=args)

    def record(self,id):
        return self._do_query(element=id)

    def delete(self,id):
        return self._do_query(action='DELETE',element=id)

    def insert(self,args):
        if 'id' in data:
            id_ = data['id']
        else:
            id_ = uuid.uuid4().hex
            data['id'] = id_
        return self._do_query(args=args)

    def _do_query(self,action='POST',rectype='record',element='_search',args={}):
        queryparam, data = self.translate(args)
        host = str(self.config.es_url).rstrip('/')
        db_path = self.config.es_db
        fullpath = '/' + db_path + '/' + rectype + '/' + element + '?' + queryparam
        c = httplib.HTTPConnection(host)
        if data:
            c.request(action, fullpath, json.dumps(data))
        else:
            c.request(action, fullpath)
        return ElasticSearchResultManager(json.loads(c.getresponse().read()), self.config, args)

    def translate(self,args):
        # translate out queryparam and args here
        queryparam = ''
        data = {}

        # first do the actual 'q' arg
        qs = []
        for field in args['q'].keys():
            if self.config.is_field_facet(field):
                for value in args['q'][field]:
                    qs.append(field + ":\"" + value + "\"")
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
        data['query'] = {"query_string":{"query":q}}
        
        # start position (for paging)
        if args.has_key("start"):
            data["from"] = args["start"]
        
        # facet mincount from config
        #solr_args["facet.mincount"] = self.config.facet_mincount
        
        # number of rows to return
        if args.has_key("rows"):
            data["size"] = args["rows"]
            
        # plain facet fields
        if args.has_key("facet_field"):
            #for item in args["facet_field"]:
            #    data["facets"][item] = {item:{"terms":{"field":i+self.config.es_exact_facet_field}}}
            data["facets"] = {i:{"terms":{"field":i+self.config.es_exact_facet_field}} for i in args["facet_field"]}
        
        # sort options
        if args.has_key("sort"):
            sort_parts = {}
            for sort_field, direction in args['sort']:
                sort_parts[sort_field] = {"order": direction}
            data["sort"] = sort_parts

        return queryparam, data


class ElasticSearchResultManager(ResultManager):
    def __init__(self, results, config, args):
        print "HELLO", results
        ResultManager.__init__(self, results, config, args)

    def get_ordered_facets(self, facet_name):
        if self.config.is_field_facet(facet_name):
            facets = []
            for term in self.results['facets'][facet_name]['terms']:
                facets.append(term['term'], term['count'])
            return facets
        return False
    
    def has_values(self, facet_name):
        if self.config.is_field_facet(facet_name):
            return self.results['facets'][facet_name]['total']
        return False
    
    def is_start(self):
        return self.args.get('start',0) == 0
        
    def is_end(self):
        return self.args.get('start',0) + self.args.get('rows',0) >= self.numFound()
    
    def start(self):
        return self.args.get('start',0)
        
    def finish(self):
        return self.args.get('start',0) + self.set_size()
        
    def start_offset(self, off):
        return self.args.get('start',0) + off
        
    def set_size(self):
        return len(self.results['hits']['hits'])
        
    def numFound(self):
        return int(self.results['hits']['total'])
        
    def set(self):
        return [rec['_source'] for rec in self.results['hits']['hits']]
    
    def last_page_start(self):
        return self.numFound() - (self.numFound() % self.args['rows'])
        
    def get_previous(self, num):
        pairs = []
        for i in range(num + 1, 0, -1):
            first = self.start() - (self.args['rows'] * i)
            if first >= self.args['rows']: # i.e. greater than the first page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
    def get_next(self, num):
        pairs = []
        for i in range(1, num + 1):
            first = self.start() + (self.args['rows'] * i)
            last_page_size = self.numFound() % self.args['rows']
            if first + self.args['rows'] <= self.numFound() - last_page_size: # i.e. less than the last page
                pairs.append((first, first + self.args['rows']))
        return sorted(pairs, key=operator.itemgetter(0))
        
