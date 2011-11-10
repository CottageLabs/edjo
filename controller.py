import json, urllib2
from core import Configuration, IndexFactory, UrlManager, TemplateFactory
from negotiator import ContentNegotiator

# create a global configuration
global_configuration = Configuration()

class SolrEyesGenericController(object):
    def GET(self, path=None):
        """
        method to handle GET request; override this in specific controllers
        
        GET request will contain the following features
        - path: a path attached to the end of the base url containing implicit facet info
        - a: a query argument containing the search constraints in JSON
        - q: a free text search query argument
        """
        self.config = global_configuration
        
    def process(self, a, q, path):
        # turn the incoming arguments to the args parameter
        initial_request, args = self._construct_args(a, q)
        
        # fold in the free text search options if relevant
        implicit_facets = self._add_implicit_facets(path, args)
        
        if len(implicit_facets) > 0:
            initial_request = False
        
        properties = self._ui_properties(args, implicit_facets)
        
        # create a search engine connection and get the results back
        index_factory = IndexFactory(self.config)
        s = index_factory.get_index_dao()
        
        if initial_request:
            properties['results'] = s.initial(args)
        else:
            properties['results'] = s.search(args)
        
        if args.has_key("search"):
            properties['q'] = args['search']
        else:
            properties['q'] = ""
            
        return properties
    
    def _ui_properties(self, args, implicit_facets):
        properties = {}
        properties['config'] = self.config
        
        # set the implicit facets for the UI to use
        properties['implicit_facets'] = implicit_facets
        
        # set the UrlManager for the UI to use
        properties['url_manager'] = UrlManager(self.config, args, implicit_facets)
        
        return properties
    
    def _construct_args(self, a, q):
        args = None
        if a is not None:
            a = urllib2.unquote(a)
            args = json.loads(a)
        
        initial_request = False
        if args is None:
            args = self.config.get_default_args()
            initial_request = True
        
        if q is not None and q != "":
            initial_request = False
            args["search"] = q
        
        return initial_request, args
        
    def _add_implicit_facets(self, path, args):
        implicit_facets = {}
        if path is not None:
            # split the path by the middle "/"
            path = path.strip()
            if path.endswith("/"):
                path = path[:-1]
            bits = path.split('/')
            if len(bits) % 2 == 0:
                self.config.base_url = self.config.base_url + path
                if not args.has_key('q'):
                    args['q'] = {}
                for i in range(0, len(bits), 2):
                    field = bits[i]
                    value = bits[i+1]
                    if args['q'].has_key(field):
                        args['q'][field].append(value)
                    else:
                        args['q'][field] = [value]
                    if implicit_facets.has_key(field):
                        implicit_facets[field].append(value)
                    else:
                        implicit_facets[field] = [value]
        return implicit_facets
    
    def _get_suffix(self, path):
        bits = path.split("/")
        last_path_part = bits[-1]
        file_parts = last_path_part.split(".")
        if len(file_parts) > 1:
            return file_parts[-1]
        return None
    
    def get_accept_parameters(self, accept, accept_language):
        # do the content negotiation
        cn = ContentNegotiator(default_accept_parameters=self.config.accepts_default, 
                                acceptable=self.config.accepts, weights=self.config.conneg_weights)
        ap = cn.negotiate(accept=accept, accept_language=accept_language)
        return ap
    
    def get_mimetype(self, suffix, accept_parameters):
        if suffix is not None:
            return self.config.get_mimetype(suffix)
        else:
            return self.config.get_mimetype(accept_parameters)
    
    def render(self, properties, suffix, accept_parameters):
        # call the render engine
        template_factory = TemplateFactory(self.config)
        t = template_factory.get_template_engine()
        return t.render(properties, suffix, accept_parameters)