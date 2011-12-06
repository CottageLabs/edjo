import web
from controller import EdjoGenericIndexController, EdjoGenericRecordController

urls = (
    '/record/(.*)', 'EdjoWebPyRecordController',
	'/(.*)', 'EdjoWebPyIndexController',
)

class EdjoWebPyIndexController(EdjoGenericIndexController):

    def GET(self, path=None):
        # call the parent to initialise
        EdjoGenericIndexController.GET(self, path)
        
        # get the "a" argument
        a = web.input().get("a")
        
        # get the "q" argument
        q = web.input().get("q")
        
        # process the request and get the UI properties back
        properties = self.process(a, q, path)
        
        # We don't want to do anything with those properties, so
        # go straight to render
        
        # we need to content negotiate, so get the accept headers out
        # of the request
        accept = web.ctx.env.get("HTTP_ACCEPT")
        accept_lang = web.ctx.env.get("HTTP_ACCEPT_LANGUAGE")
        accept_parameters = self.get_accept_parameters(accept, accept_lang)
        if accept_parameters is None:
            # 415 the client
            # FIXME: is this how this works?
            web.status = 415
        
        suffix = self._get_suffix(path)
        
        # get the mimetype for the return type
        mimetype = self.get_mimetype(suffix, accept_parameters)
        web.header("Content-Type", mimetype)
        
        return self.render_index(properties, suffix, accept_parameters)

class EdjoWebPyRecordController(EdjoGenericRecordController):

    def GET(self, id):
        # call the parent to initialise
        EdjoGenericRecordController.GET(self, id)
        
        # get the "a" argument
        a = web.input().get("a")
        
        # get the "q" argument
        q = web.input().get("q")
        
        # process the request and get the UI properties back
        properties = self.process(a, q, id)
        
        # we need to content negotiate, so get the accept headers out
        # of the request
        accept = web.ctx.env.get("HTTP_ACCEPT")
        accept_lang = web.ctx.env.get("HTTP_ACCEPT_LANGUAGE")
        accept_parameters = self.get_accept_parameters(accept, accept_lang)
        if accept_parameters is None:
            # 415 the client
            # FIXME: is this how this works?
            web.status = 415
        
        suffix = self._get_suffix(id)
        
        # get the mimetype for the return type
        mimetype = self.get_mimetype(suffix, accept_parameters)
        web.header("Content-Type", mimetype)
        
        return self.render_record(properties, suffix, accept_parameters)

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()