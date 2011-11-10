import os
from mako.lookup import TemplateLookup
from mako.template import Template
from StringIO import StringIO
from mako.runtime import Context
from template import TemplateEngine

class MakoTemplate(TemplateEngine):
    def __init__(self, config):
        self.config = config
    
    def render(self, properties, suffix, accept_parameters):
        # set the template resource path
        res_path = os.path.join(os.path.dirname(__file__), 'templates')
        
        format = None
        template_name = None
        lang = str(accept_parameters.language)
        
        if suffix is not None:
            print suffix
            format = self.config.get_format_name(suffix)
            template_name = self.config.get_template_name(suffix)
        else:
            format = self.config.get_format_name(accept_parameters)
            template_name = self.config.get_template_name(accept_parameters)
        
        if format is None or template_name is None:
            # actually, this is not acceptable, so we should return a 415
            return None
        
        # The Mako templates are in templates/[lang]/[format]/[template_name]/index.mako
        fn = os.path.join(res_path, lang, format, template_name, "index.mako")
        lookup = os.path.join(res_path, lang, format, template_name)
        
        # there is an optional _lib directory for all the templates
        lib_dir = os.path.join(res_path, lang, format, "_lib")
        
        # build the template and send back the output
        mylookup = TemplateLookup(directories=[lookup, lib_dir])
        
        t = Template(filename=fn, lookup=mylookup)
        buf = StringIO()
        ctx = Context(buf, c=properties)
        t.render_context(ctx)
        return buf.getvalue()
        