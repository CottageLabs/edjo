import os
from mako.lookup import TemplateLookup
from mako.template import Template
from StringIO import StringIO
from mako.runtime import Context
from template import TemplateEngine

class MakoTemplate(TemplateEngine):
    def __init__(self, config):
        self.config = config
    
    def render_record(self, properties, suffix, accept_parameters):
        template_path, lookup, lib_dir = self._get_template_paths(suffix, accept_parameters)
        fn = os.path.join(template_path, "record.mako")
        return self._render(fn, [lookup, lib_dir], properties)
    
    def render_index(self, properties, suffix, accept_parameters):
        template_path, lookup, lib_dir = self._get_template_paths(suffix, accept_parameters)
        fn = os.path.join(template_path, "index.mako")
        dirs = [lookup, lib_dir]
        return self._render(fn, dirs, properties)
    
    def _render(self, template_file, lookup_dirs, properties):
        # build the template and send back the output
        mylookup = TemplateLookup(directories=lookup_dirs)
        
        t = Template(filename=template_file, lookup=mylookup)
        buf = StringIO()
        ctx = Context(buf, c=properties)
        t.render_context(ctx)
        return buf.getvalue()
    
    def _get_template_paths(self, suffix, accept_parameters):
        # set the template resource path
        res_path = os.path.join(os.path.dirname(__file__), 'templates')
        
        format = None
        template_name = None
        lang = str(accept_parameters.language)
        
        if suffix is not None:
            format = self.config.get_format_name(suffix)
            template_name = self.config.get_template_name(suffix)
        else:
            format = self.config.get_format_name(accept_parameters)
            template_name = self.config.get_template_name(accept_parameters)
        
        if format is None or template_name is None:
            # actually, this is not acceptable, so we should return a 415
            return None, None, None
        
        # The Mako templates are in templates/[lang]/[format]/[template_name]/index.mako
        template_path = os.path.join(res_path, lang, format, template_name)
        lookup = os.path.join(res_path, lang, format, template_name)
        
        # there is an optional _lib directory for all the templates
        lib_dir = os.path.join(res_path, lang, format, "_lib")
        
        return template_path, lookup, lib_dir