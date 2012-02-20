import json, urllib2
from copy import deepcopy
from pkg_resources import resource_stream
from negotiator import AcceptParameters, ContentType, Language
import functions as function_lib

class SortOption(object):
    def __init__(self, field, display):
        self.field = field
        self.display = display

class Field(object):
    def __init__(self, field, display, value_functions=None):
        self.field = field
        self.display = display
        self.value_functions = value_functions
        
    def get_value(self, args, result): pass
    def get_value_array(self, args, result): pass

class ValueField(Field):
    def __init__(self, field, display, value_functions=None):
        Field.__init__(self, field, display, value_functions)
        
    def get_value(self, args, result):
        value = result.get(self.field)
        if hasattr(value, "append"):
            parts = []
            for val in value:
                parts.append(self._pipeline(val))
            return ", ".join(parts)
        else:
            return self._pipeline(value)
            
    def get_value_array(self, args, result):
        arr = []
        value = result.get(self.field)
        if hasattr(value, "append"):
            for val in value:
                arr.append(self._pipeline(val))
        else:
            arr.append(self._pipeline(value))
        return arr
            
    def _pipeline(self, value):
        value = unicode(value)
        if self.value_functions is None:
            return value
        for func in self.value_functions:
            value = func.run(value)
        return value

class DynamicField(Field):
    def __init__(self, field, display, generator_functions=None):
        Field.__init__(self, field, display, None)
        self.generator_functions = generator_functions
        
    def get_value(self, args, result):
        value = None
        if self.generator_functions is None:
            return value
        for func in self.generator_functions:
            value = func.run(args, result, value)
        return value

class Facet(object):
    def __init__(self, field, display, value_functions=None):
        self.field = field
        self.display = display
        self.value_functions = value_functions
        
    def get_value(self, v):
        value = unicode(v)
        if self.value_functions is None:
            return value
        for func in self.value_functions:
            value = func.run(value)
        return value
        
    def __repr__(self):
        return self.field + "; " + self.display

class FieldFacet(Facet):
    def __init__(self, field, display, value_functions=None):
        Facet.__init__(self, field, display, value_functions)
        
    def __repr__(self):
        return "Field Facet: " + Facet.__repr__(self)

class DateFacet(Facet):
    def __init__(self, field, display, min, max, gap, mincount, value_functions=None, upper_display_functions=None):
        Facet.__init__(self, field, display, value_functions)
        self.min = min
        self.max = max
        self.gap = gap
        self.mincount = mincount
        self.upper_display_functions=upper_display_functions
        
    def display_upper(self, lower, upper):
        if self.upper_display_functions is None:
            return True
        for func in self.upper_display_functions:
            disp = func.run(lower, upper)
            if disp is False:
                return False
        return True
    
    def __repr__(self):
        return "Date Facet: " + Facet.__repr__(self)

class RangeFacet(Facet):
    def __init__(self, field, display, min, max, gap, mincount, infinity, value_functions=None, upper_display_functions=None):
        Facet.__init__(self, field, display, value_functions)
        self.min = min
        self.max = max
        self.gap = gap
        self.mincount = mincount
        self.infinity = infinity
    
    def display_upper(self, lower, upper):
        if self.upper_display_functions is None:
            return True
        for func in self.upper_display_functions:
            disp = func.run(lower, upper)
            if disp is False:
                return False
        return True
        
    def __repr__(self):
        return "Range Facet: " + Facet.__repr__(self)
    
class QueryFacet(Facet):
    def __init__(self, field, display, queries, value_functions=None):
        Facet.__init__(self, field, display, value_functions)
        self.queries = queries
        
    def __repr__(self):
        return "Query Facet: " + Facet.__repr__(self)

class PipelineFunction(object):
    def __init__(self, function, function_args):
        self.function = function
        self.function_args = function_args
        
    def run(self, *params):
        return self.function(self.function_args, *params)

class IndexFactory(object):

    def __init__(self, config):
        self.config = config

    def get_index_dao(self):
        mod = __import__(self.config.index_engine)
        inst = getattr(mod, self.config.index_class)(self.config)
        return inst
        
class TemplateFactory(object):

    def __init__(self, config):
        self.config = config

    def get_template_engine(self):
        mod = __import__(self.config.template_engine)
        inst = getattr(mod, self.config.template_class)(self.config)
        return inst
        
class Configuration(object):
    def __init__(self):
        # extract the configuration from the json object
        self.cfg = self._load_json()
        
        # create content negotiation objects
        self.accepts, self.accepts_default, self.conneg_weights = self._load_conneg()
        
        # load the configuration components
        self.facets = self._load_facets()
        self.fields = self._load_fields()
        self.sort = self._load_sort()
        self.record = self._load_record()
    
    def get_facet(self, facet_name):
        for facet in self.facets:
            if facet.field == facet_name:
                return facet
        return None
    
    def get_field(self, field_name):
        for field in self.fields:
            if field.field == field_name:
                return field
        return None
    
    def get_default_args(self):
        fields = []
        ranges = []
        dates = []
        queries = []
        for facet in self.facets:
            if isinstance(facet, FieldFacet):
                fields.append(facet.field)
            elif isinstance(facet, RangeFacet):
                ranges.append(facet.field)
            elif isinstance(facet, DateFacet):
                dates.append(facet.field)
            elif isinstance(facet, QueryFacet):
                queries.append(facet.field)
        return {
            "q" : {},
            "start" : 0,
            "facet_field" : fields,
            "facet_range" : ranges,
            "facet_date" : dates,
            "rows" : self.default_results_per_page
        }
        
    def is_field_facet(self, field_name):
        for facet in self.facets:
            if facet.field == field_name:
                if isinstance(facet, FieldFacet):
                    return True
                else:
                    return False
        return False
        
    def is_date_facet(self, field_name):
        for facet in self.facets:
            if facet.field == field_name:
                if isinstance(facet, DateFacet):
                    return True
                else:
                    return False
        return False
    
    def is_range_facet(self, field_name):
        for facet in self.facets:
            if facet.field == field_name:
                if isinstance(facet, RangeFacet):
                    return True
                else:
                    return False
        return False
    
    def is_query_facet(self, field_name):
        for facet in self.facets:
            if facet.field == field_name:
                if isinstance(facet, QueryFacet):
                    return True
                else:
                    return False
        return False
    
    def get_format_name(self, accept_parameters_or_suffix):
        acceptable = acceptable = self._get_acceptable(accept_parameters_or_suffix)
        if acceptable is not None:
            return acceptable.get('format_name')
        return None
        
    def get_template_name(self, accept_parameters_or_suffix):
        acceptable = self._get_acceptable(accept_parameters_or_suffix)
        if acceptable is not None:
            return acceptable.get('template_name')
        return None
        
    def get_mimetype(self, accept_parameters_or_suffix):
        acceptable = self._get_acceptable(accept_parameters_or_suffix)
        if acceptable is not None:
            return acceptable.get('mimetype')
        return "application/octet-stream"
    
    def get_sort_option(self, option):
        for so in self.sort:
            if so.field == option:
                return so
        return None
    
    def _get_acceptable(self, accept_parameters_or_suffix):
        acceptable = None
        if isinstance(accept_parameters_or_suffix, AcceptParameters):
            acceptable = self._acceptable_from_conneg(accept_parameters_or_suffix)
        else:
            acceptable = self._acceptable_from_suffix(accept_parameters_or_suffix)
        return acceptable
    
    def _acceptable_from_conneg(self, accept_parameters):
        for acceptable in self.cfg['conneg']['acceptable']:
            if (acceptable.get('mimetype') == accept_parameters.content_type.mimetype()
                    and acceptable.get('language') == str(accept_parameters.language)):
                return acceptable
        return None
        
    def _acceptable_from_suffix(self, suffix):
        for acceptable in self.cfg['conneg']['acceptable']:
            if acceptable.get('suffix') == suffix:
                return acceptable
        return None
    
    def _load_json(self):
        f = resource_stream(__name__, 'config.json')
        c = ""
        for line in f:
            if line.strip().startswith("#"):
                c+= "\n" # this makes it easier to debug the config
            else:
                c += line
        return json.loads(c)
    
    def _load_record(self):
        record = []
        for field in self.cfg['record']:
            funcs = None
            vfs = field.get('value_functions')
            if vfs is not None:
                funcs = self._load_functions(vfs)
            f = ValueField(field.get('field'), field.get('display'), funcs)
            record.append(f)
        return record
    
    def _load_conneg(self):
        default = self.cfg['conneg']['default']
        acceptable = self.cfg['conneg']['acceptable']
        weights = self.cfg['conneg']['weights']
        
        default_accepts = AcceptParameters(ContentType(default.get('mimetype')), Language(default.get('language')))
        accept_parameters = []
        for a in acceptable:
            lang = a.get('language', default.get('language'))
            mime = a.get('mimetype', default.get('mimetype'))
            accept_parameters.append(AcceptParameters(ContentType(mime), Language(lang)))
        
        return accept_parameters, default_accepts, weights
    
    def _load_facets(self):
        facets = []
        for facet in self.cfg['facets']:
            if facet['type'] == "field":
                facets.append(self._load_field_facet(facet))
            elif facet['type'] == "date":
                facets.append(self._load_date_facet(facet))
            elif facet['type'] == "range":
                facets.append(self._load_range_facet(facet))
            elif facet['type'] == "query":
                facets.append(self._load_query_facet(facet))
        return facets
    
    def _load_fields(self):
        fields = []
        for field in self.cfg['fields']:
            if field['type'] == 'value':
                fields.append(self._load_value_field(field))
            elif field['type'] == 'dynamic':
                fields.append(self._load_dynamic_field(field))
        return fields
    
    def _load_sort(self):
        sort_fields = self.cfg['sort']
        sort_options = []
        for s in sort_fields:
            so = SortOption(s.get("field"), s.get("display"))
            sort_options.append(so)
        return sort_options
    
    def _load_value_field(self, field):
        funcs = None
        vfs = field.get('value_functions')
        if vfs is not None:
            funcs = self._load_functions(vfs)
        f = ValueField(field.get('field'), field.get('display'), funcs)
        return f
    
    def _load_dynamic_field(self, field):
        funcs = None
        vfs = field.get('generator_functions')
        if vfs is not None:
            funcs = self._load_functions(vfs)
        f = DynamicField(field.get('field'), field.get('display'), funcs)
        return f
    
    def _load_field_facet(self, facet):
        funcs = None
        vfs = facet.get('value_functions')
        if vfs is not None:
            funcs = self._load_functions(vfs)
        f = FieldFacet(facet.get('field'), facet.get('display'), funcs)
        return f
    
    def _load_date_facet(self, facet):
        vfuncs = None
        vfs = facet.get('value_functions')
        if vfs is not None:
            vfuncs = self._load_functions(vfs)
        ufuncs = None
        udfs = facet.get('upper_display_functions')
        if udfs is not None:
            ufuncs = self._load_functions(udfs)
        f = DateFacet(facet.get('field'), facet.get('display'), facet.get('min'),
                        facet.get('max'), facet.get('gap'), facet.get('mincount'), vfuncs, ufuncs)
        return f
    
    def _load_query_facet(self, facet):
        funcs = None
        vfs = facet.get('value_functions')
        if vfs is not None:
            funcs = self._load_value_functions(vfs)
        f = QueryFacet(facet.get('field'), facet.get('display'), facet.get('queries'), funcs)
        return f
    
    def _load_range_facet(self, facet):
        vfuncs = None
        vfs = facet.get('value_functions')
        if vfs is not None:
            vfuncs = self._load_functions(vfs)
        udfs = facet.get('upper_display_functions')
        ufuncs = None
        if udfs is not None:
            ufuncs = self._load_functions(udfs)
        f = RangeFacet(facet.get('field'), facet.get('display'), facet.get('min'),
                        facet.get('max'), facet.get('gap'), facet.get('mincount'), 
                        facet.get('infinity'), vfuncs, ufuncs)
        return f
    
    def _load_functions(self, fs):
        functions = []
        for function in fs:
            func_name = function.keys()[0]
            args = function[func_name]
            func = getattr(function_lib, func_name)
            functions.append(PipelineFunction(func, args))
        return functions
    
    def __getattr__(self, attr):
        return self.cfg.get(attr, None)


class UrlManager(object):
    def __init__(self, config, args=None, implicit_facets=None):
        self.config = config
        self.args = args if args is not None else self.config.get_default_args()
        self.implicit_facets = implicit_facets
        self.base_args = self.strip_implicit_facets()
    
    def strip_implicit_facets(self):
        myargs = deepcopy(self.args)
        if self.implicit_facets is None:
            return myargs
        if not self.args.has_key('q'):
            return myargs
        
        for field in self.implicit_facets.keys():
            if myargs['q'].has_key(field):
                del myargs['q'][field]
        return myargs
    
    def get_base_url(self):
        burl = self.config.base_url
        for key in self.implicit_facets.keys():
            burl += key
            for v in self.implicit_facets[key]:
                burl += "/" + v
        return burl
    
    def get_search_form_action(self):
        return self.config.base_url
    
    def get_form_field_args(self):
        myargs = deepcopy(self.base_args)
        if myargs.has_key("search"):
            del myargs['search']
        j = json.dumps(myargs)
        return urllib2.quote(j)
    
    def get_add_url(self, field, value, upper=None):
        myargs = deepcopy(self.base_args)
        if myargs["q"].has_key(field):
            if upper is None and value not in myargs["q"][field]:
                myargs["q"][field].append(value)
            elif upper is not None:
                myargs["q"][field] = [value, upper]
        else:
            if upper is None:
                myargs["q"][field] = [value]
            else:
                myargs["q"][field] = [value, upper]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_add_date_url(self, field, value, upper=None):
        myargs = deepcopy(self.base_args)
        value = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(value, '02')
        if upper is not None and upper != -1:
            upper = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(upper, '02')
        if myargs["q"].has_key(field):
            if upper is None and value not in myargs["q"][field]:
                myargs["q"][field].append(value)
            elif upper is not None:
                myargs["q"][field] = [value, upper]
        else:
            if upper is None:
                myargs["q"][field] = [value]
            else:
                myargs["q"][field] = [value, upper]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)

    def get_delete_url(self, field, value=None):
        myargs = deepcopy(self.base_args)
        if value is not None:
            myargs['q'][field].remove(value)
            if len(myargs['q'][field]) == 0:
                del myargs['q'][field]
        else:
            del myargs['q'][field]
        if myargs.has_key('start'):
            del myargs['start']
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_position_url(self, position):
        myargs = deepcopy(self.base_args)
        myargs["start"] = position
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_rpp_url(self, rpp):
        myargs = deepcopy(self.base_args)
        myargs["rows"] = int(rpp)
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_sort_url(self, field, direction):
        myargs = deepcopy(self.base_args)
        if myargs.has_key("sort"):
            isnew = True
            for i in range(len(myargs['sort'])):
                f, d = myargs['sort'][i]
                if f == field:
                    myargs['sort'][i] = [field, direction]
                    isnew = False
                    break
            if isnew:
                myargs['sort'].append([field, direction])
        else:
            myargs["sort"] = [[field, direction]]
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_unsort_url(self, field):
        myargs = deepcopy(self.base_args)
        for i in range(len(myargs['sort'])):
            f, direction = myargs['sort'][i]
            if f == field:
                del myargs['sort'][i]
                break
        j = json.dumps(myargs)
        return self.config.base_url + "?a=" + urllib2.quote(j)
        
    def get_record_url(self, record):
        id = record.get(self.config.unique_id_field)
        base = self.config.record_base_url
        if not base.endswith("/"):
            base = base + "/"
        record_url = base + str(id)
        j = json.dumps(self.base_args)
        return record_url + "?a=" + urllib2.quote(j)
        
    def get_this_url(self):
        j = json.dumps(self.base_args)
        return self.config.base_url + "?a=" + urllib2.quote(j)
