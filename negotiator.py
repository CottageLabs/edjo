# CONTENT NEGOTIATION
#######################################################################
# A sort of generic tool for carrying out content negotiation tasks for 
# the web interface

class AcceptParameters(object):
    def __init__(self, content_type=None, language=None, encoding=None, charset=None):
        self.content_type = content_type
        self.language = language
        self.encoding = encoding
        self.charset = charset
        
    def matches(self, other, ignore_language_variants=False, as_client=True):
        if other is None:
            return False
        ct_match = self.content_type.matches(other.content_type) if self.content_type is not None else True
        e_match = self.encoding == other.encoding
        c_match = self.charset == other.charset
        l_match = self.language.matches(other.language, ignore_language_variants, as_client) if self.language is not None else True
        
        return ct_match and l_match and e_match and c_match
        
    def __str__(self):
        s = "AcceptParameters:: "
        if self.content_type is not None:
            s += "Content Type: " + str(self.content_type) + ";"
        if self.language is not None:
            s += "Language: " + str(self.language) + ";"
        if self.encoding is not None:
            s += "Encoding: " + str(self.encoding) + ";"
        if self.charset is not None:
            s += "Charset: " + str(self.charset) + ";"
        return s
    
    def __repr__(self):
        return str(self)

class Language(object):
    def __init__(self, range=None, language=None, variant=None):        
        if range is not None:
            self.language, self.variant = self._from_range(range)
        else:
            self.language = language
            self.variant = variant
        
    def matches(self, other, ignore_language_variants=False, as_client=True):
        if other is None:
            return False
        
        if self.language == "*" or other.language == "*":
            return True
        
        l_match = self.language == other.language
        v_match = self.variant == other.variant
        
        if as_client and self.variant is None and other.variant is not None:
            v_match = True
        elif as_client and self.variant is not None and other.variant is None:
            if ignore_language_variants:
                v_match = True
        
        return l_match and v_match
    
    def _from_range(self, range):
        lang_parts = range.split("-")
        if len(lang_parts) == 1:
            return lang_parts[0], None
        elif len(lang_parts) == 2:
            lang = lang_parts[0]
            sublang = lang_parts[1]
            return lang, sublang
    
    def __str__(self):
        s = str(self.language)
        if self.variant is not None:
            s += "-" + str(self.variant)
        return s
            
    def __repr__(self):
        return str(self)

class ContentType(object):
    """
    Class to represent a content type requested through content negotiation
    """
    def __init__(self, mimetype=None, type=None, subtype=None, params=None):
        """
        Properties:
        type    - the main type of the content.  e.g. in text/html, the type is "text"
        subtype - the subtype of the content.  e.g. in text/html the subtype is "html"
        params  - as per the mime specification, his represents the parameter extension to the type, e.g. with
                    application/atom+xml;type=entry, the params are "type=entry"

        So, for example:
        application/atom+xml;type=entry => type="application", subtype="atom+xml", params="type=entry"
        """
        self.type = None
        self.subtype = None
        self.params = None
        
        if mimetype is not None:
            self.from_mimetype(mimetype)
        else:
            self.type = type
            self.subtype = subtype
            self.params = params

    def from_mimetype(self, mimetype):
        # mimetype is of the form <supertype>/<subtype>[;<params>]
        parts = mimetype.split(";")
        if len(parts) == 2:
            self.type, self.subtype = parts[0].split("/", 1)
            self.params = parts[1]
        elif len(parts) == 1:
            self.type, self.subtype = parts[0].split("/", 1)

    def mimetype(self):
        """
        Turn the content type into its mimetype representation
        """
        mt = self.type + "/" + self.subtype
        if self.params is not None:
            mt += ";" + self.params
        return mt

    def matches(self, other):
        """
        Determine whether this ContentType and the supplied other ContentType are matches.  This includes full equality
        or whether the wildcards (*) which can be supplied for type or subtype properties are in place in either
        partner in the match.
        """
        # assume None to be a wildcard
        if other is None:
            return False
        
        tmatch = self.type == "*" or other.type == "*" or self.type == other.type
        smatch = self.subtype == "*" or other.subtype == "*" or self.subtype == other.subtype
        # FIXME: there is some ambiguity in mime as to whether the omission of the params part is the same as
        # a wildcard.  For the purposes of convenience we have assumed here that it is, otherwise a request for
        # */* will not match any content type which has parameters
        pmatch = self.params is None or other.params is None or self.params == other.params

        return tmatch and smatch and pmatch

    def __eq__(self, other):
        return self.mimetype() == other.mimetype()

    def __str__(self):
        return self.mimetype()

    def __repr__(self):
        return str(self)

class ContentNegotiator(object):
    """
    Class to manage content negotiation.  Given its input parameters it will provide a ContentType object which
    the server can use to locate its resources
    """
    def __init__(self, default_accept_parameters=None, acceptable=[], weights=None, ignore_language_variants=False):
        """
        There are 4 parameters which must be set in order to start content negotiation
        - acceptable    -   What AcceptParameter objects are acceptable to return (in order of preference)
        - default_accept_parameters - the parameters to use when all or part of the analysed accept headers is not present
        """
        self.acceptable = acceptable
        self.default_accept_parameters = default_accept_parameters
        self.weights = weights if weights is not None else {'content_type' : 1.0, 'language' : 1.0, 'charset' : 1.0, 'encoding' : 1.0}
        self.ignore_language_variants = ignore_language_variants
        
        if not self.weights.has_key("content_type"):
            self.weights["content_type"] = 1.0
        if not self.weights.has_key("language"):
            self.weights["language"] = 1.0
        if not self.weights.has_key("charset"):
            self.weights["charset"] = 1.0
        if not self.weights.has_key("encoding"):
            self.weights["encoding"] = 1.0

    def negotiate(self, accept=None, accept_language=None, accept_encoding=None, accept_charset=None):
        """
        Main method for carrying out content negotiation over the supplied HTTP headers.
        Returns either the preferred ContentType as per the settings of the object, or None if no agreement could be
        reached
        """
        
        if accept is None and accept_language is None and accept_encoding is None and accept_charset is None:
            # if it is not available just return the defaults
            return self.default_accept_parameters

        print "Accept: " + str(accept)
        print "Accept-Language: " + str(accept_language)

        # get us back a dictionary keyed by q value which tells us the order of preference that the client has
        # requested
        accept_analysed = self._analyse_accept(accept)
        lang_analysed = self._analyse_language(accept_language)
        encoding_analysed = self._analyse_encoding(accept_encoding)
        charset_analysed = self._analyse_charset(accept_charset)
        
        print "Accept Analysed: " + str(accept_analysed)
        print "Language Analysed: " + str(lang_analysed)
        
        # now combine these results into one list of preferred accepts
        preferences = self._list_acceptable(self.weights, accept_analysed, lang_analysed, encoding_analysed, charset_analysed)
        
        print "Preference List: " + str(preferences)
        
        # go through the analysed formats and cross reference them with the acceptable formats
        accept_parameters = self._get_acceptable(preferences, self.acceptable)
        
        print "Acceptable: " + str(accept_parameters)

        # return the acceptable type.  If this is None (which get_acceptable can return), then the caller
        # will know that we failed to negotiate a type and should 415 the client
        return accept_parameters

    def _list_acceptable(self, weights, content_types=None, languages=None, encodings=None, charsets=None):
        
        print "Relative weights: " + str(weights)
        
        if content_types is None:
            content_types = {0.0 : [None]}
        if languages is None:
            languages = {0.0 : [None]}
        if encodings is None:
            encodings = {0.0 : [None]}
        if charsets is None:
            charsets = {0.0 : [None]}
        
        print "Matrix of options"
        print content_types
        print languages
        print encodings
        print charsets
        
        unsorted = []
        
        # create an accept_parameter for each first precedence field
        for q1, vals1 in content_types.items():
            for v1 in vals1:
                for q2, vals2 in languages.items():
                    for v2 in vals2:
                        for q3, vals3 in encodings.items():
                            for v3 in vals3:
                                for q4, vals4 in charsets.items():
                                    wq = ((weights['content_type'] * q1) + (weights['language'] * q2) +
                                            (weights['encoding'] * q3) + (weights['charset'] * q4))
                                    for v4 in vals4:
                                        ap = AcceptParameters(v1, v2, v3, v4)
                                        unsorted.append((ap, wq))
        
        sorted = self._sort_by_q(unsorted, 0.0)
        return sorted

    def _analyse_encoding(self, accept):
        return None
        
    def _analyse_charset(self, accept):
        return None

    def _analyse_language(self, accept):
        if accept is None:
            return None
        parts = self._split_accept_header(accept)
        highest_q = 0.0
        counter = 0
        unsorted = []
        for part in parts:
            counter += 1
            lang, sublang, q = self._interpret_accept_language_field(part, -1 * counter)
            if q > highest_q:
                highest_q = q
            unsorted.append((Language(language=lang, variant=sublang), q))
        sorted = self._sort_by_q(unsorted, highest_q)

        # now we have a dictionary keyed by q value which we can return
        return sorted

    def _analyse_accept(self, accept):
        """
        Analyse the Accept header string from the HTTP headers and return a structured dictionary with each
        content types grouped by their common q values, thus:

        dict = {
            1.0 : [<ContentType>, <ContentType>],
            0.8 : [<ContentType],
            0.5 : [<ContentType>, <ContentType>]
        }

        This method will guarantee that every content type has some q value associated with it, even if this was not
        supplied in the original Accept header; it will be inferred based on the rules of content negotiation
        """
        if accept is None:
            return None
            
        # the accept header is a list of content types and q values, in a comma separated list
        parts = self._split_accept_header(accept)

        # set up some registries for the coming analysis.  unsorted will hold each part of the accept header following
        # its analysis, but without respect to its position in the preferences list.  highest_q and counter will be
        # recorded during this first run so that we can use them to sort the list later
        unsorted = []
        highest_q = 0.0
        counter = 0

        # go through each possible content type and analyse it along with its q value
        for part in parts:
            # count the part number that we are working on, starting from 1
            counter += 1
            
            type, params, q = self._interpret_accept_field(part, -1 * counter)
            supertype, subtype = type.split("/", 1)
            if q > highest_q:
                highest_q = q

            # at the end of the analysis we have all of the components with or without their default values, so we
            # just record the analysed version for the time being as a tuple in the unsorted array
            unsorted.append((ContentType(type=supertype, subtype=subtype, params=params), q))

        # once we've finished the analysis we'll know what the highest explicitly requested q will be.  This may leave
        # us with a gap between 1.0 and the highest requested q, into which we will want to put the content types which
        # did not have explicitly assigned q values.  Here we calculate the size of that gap, so that we can use it
        # later on in positioning those elements.  Note that the gap may be 0.0.
        sorted = self._sort_by_q(unsorted, highest_q)

        # now we have a dictionary keyed by q value which we can return
        return sorted

    def _sort_by_q(self, unsorted, q_max):
        # set up a dictionary to hold our sorted results.  The dictionary will be keyed with the q value, and the
        # value of each key will be an array of ContentType objects (in no particular order)
        sorted = {}

        # go through the unsorted list
        for (value, q) in unsorted:
            if q > 0:
                # if the q value is greater than 0 it was explicitly assigned in the Accept header and we can just place
                # it into the sorted dictionary
                self.insert(sorted, q, value)
            else:
                # otherwise, we have to calculate the q value using the following equation which creates a q value "qv"
                # within "q_range" of 1.0 [the first part of the eqn] based on the fraction of the way through the total
                # accept header list scaled by the q_range [the second part of the eqn]
                #qv = (1.0 - q_range) + (((-1 * q)/scale_factor) * q_range)
                q_fraction = 1.0 / (-1.0 * q) # this is the fraction of the remaining spare q values that we can assign
                qv = q_max + ((1.0 - q_max) * q_fraction) # this scales the fraction to the remaining q range and adds it onto the highest other qs (this also handles q_max = 1.0 implicitly)
                self.insert(sorted, qv, value)

        # now we have a dictionary keyed by q value which we can return
        return sorted

    def _split_accept_header(self, accept):
        return [a.strip() for a in accept.split(",")]

    def _interpret_accept_language_field(self, accept, default_q):
        components = accept.split(";")
        
        lang = None
        sublang = None
        q = default_q
        
        # the first part can be a language, or a language-sublanguage pair (like en, or en-gb)
        langs = components[0].strip()
        lang_parts = langs.split("-")
        if len(lang_parts) == 1:
            lang = lang_parts[0]
        elif len(lang_parts) == 2:
            lang = lang_parts[0]
            sublang = lang_parts[1]
            
        if len(components) == 2:
            q = components[1].strip()[2:] # strip the "q=" from the start of the q value
            
        return (lang, sublang, float(q))
        

    def _interpret_accept_field(self, accept, default_q):
    
        # the components of the part can be "type;params;q" "type;params", "type;q" or just "type"
        components = accept.split(";")
    
        # the first part is always the type (see above comment)
        type = components[0].strip()
    
        # create some default values for the other parts.  If there is no params, we will use None, if there is
        # no q we will use a negative number multiplied by the position in the list of this part.  This allows us
        # to later see the order in which the parts with no q value were listed, which is important
        params = None
        q = default_q
    
        # There are then 3 possibilities remaining to check for: "type;q", "type;params" and "type;params;q"
        # ("type" is already handled by the default cases set up above)
        if len(components) == 2:
            # "type;q" or "type;params"
            if components[1].strip().startswith("q="):
                # "type;q"
                q = components[1].strip()[2:] # strip the "q=" from the start of the q value
            else:
                # "type;params"
                params = components[1].strip()
        elif len(components) == 3:
            # "type;params;q"
            params = components[1].strip()
            q = components[1].strip()[2:] # strip the "q=" from the start of the q value
            
        return (type, params, float(q))

    def insert(self, d, q, v):
        """
        Utility method: if dict d contains key q, then append value v to the array which is identified by that key
        otherwise create a new key with the value of an array with a single value v
        """
        if d.has_key(q):
            d[q].append(v)
        else:
            d[q] = [v]

    def _contains_match(self, source, target):
        """
        Does the target list of AcceptParameters objects contain a match for the supplied source
        Args:
        - source:   An AcceptParameters object which we want to see if it matches anything in the target
        - target:   A list of AcceptParameters objects to try to match the source against
        Returns the matching AcceptParameters from the target list, or None if no such match
        """
        for ap in target:
            if source.matches(ap, ignore_language_variants=self.ignore_language_variants):
                # matches are symmetrical, so source.matches(ap) == ap.matches(source) so way round is irrelevant
                # we return the target's content type, as this is considered the definitive list of allowed
                # content types, while the source may contain wildcards
                return ap
        return None

    def _get_acceptable(self, client, server):
        """
        Take the client content negotiation requirements and the server's
        array of supported types (in order of preference) and determine the most acceptable format to return.

        This method always returns the client's most preferred format if the server supports it, irrespective of the
        server's preference.  If the client has no discernable preference between two formats (i.e. they have the same
        q value) then the server's preference is taken into account.

        Returns an AcceptParameters object represening the mutually acceptable content type, or None if no agreement could
        be reached.
        """

        print "Client: " + str(client)
        print "Server: " +  str(server)
        
        # get the client requirement keys sorted with the highest q first (the server is a list which should be
        # in order of preference already)
        ckeys = client.keys()
        ckeys.sort(reverse=True)

        # the rule for determining what to return is that "the client's preference always wins", so we look for the
        # highest q ranked item that the server is capable of returning.  We only take into account the server's
        # preference when the client has two equally weighted preferences - in that case we take the server's
        # preferred content type
        for q in ckeys:
            # for each q in order starting at the highest
            possibilities = client[q]
            allowable = []
            for p in possibilities:
                # for each accept parameter with the same q value

                # find out if the possibility p matches anything in the server.  This uses the AcceptParameter's
                # matches() method which will take into account wildcards, so content types like */* will match
                # appropriately.  We get back from this the concrete AcceptParameter as specified by the server
                # if there is a match, so we know the result contains no unintentional wildcards
                match = self._contains_match(p, server)
                if match is not None:
                    # if there is a match, register it
                    allowable.append(match)

            print "Allowable: " + str(q) + ":" + str(allowable)

            # we now know if there are 0, 1 or many allowable content types at this q value
            if len(allowable) == 0:
                # we didn't find anything, so keep looking at the next q value
                continue
            elif len(allowable) == 1:
                # we found exactly one match, so this is our content type to use
                return allowable[0]
            else:
                # we found multiple supported content types at this q value, so now we need to choose the server's
                # preference
                for i in range(len(server)):
                    # iterate through the server explicitly by numerical position
                    if server[i] in allowable:
                        # when we find our first content type in the allowable list, it is the highest ranked server content
                        # type that is allowable, so this is our type
                        return server[i]

        # we've got to here without returning anything, which means that the client and server can't come to
        # an agreement on what content type they want and can deliver.  There's nothing more we can do!
        return None

if __name__ == "__main__":
    
    print "========= CONTENT TYPE =============="
    
    print "+++ text/plain only +++"
    accept = "text/plain"
    server = [AcceptParameters(ContentType("text/plain"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml vs application/rdf+xml without q values +++"
    accept = "application/atom+xml, application/rdf+xml"
    server = [AcceptParameters(ContentType("application/rdf+xml")), AcceptParameters(ContentType("application/atom+xml"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml vs application/rdf+xml with q values +++"
    accept = "application/atom+xml;q=0.6, application/rdf+xml;q=0.9"
    server = [AcceptParameters(ContentType("application/rdf+xml")), AcceptParameters(ContentType("application/atom+xml"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml vs application/rdf+xml vs text/html with mixed q values +++"
    accept = "application/atom+xml;q=0.6, application/rdf+xml;q=0.9, text/html"
    server = [AcceptParameters(ContentType("application/rdf+xml")), AcceptParameters(ContentType("application/atom+xml")),
                AcceptParameters(ContentType("text/html"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ text/plain only, unsupported by server +++"
    accept = "text/plain"
    server = [AcceptParameters(ContentType("text/html"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml vs application/rdf+xml vs text/html with mixed q values, most preferred unavailable +++"
    accept = "application/atom+xml;q=0.6, application/rdf+xml;q=0.9, text/html"
    server = [AcceptParameters(ContentType("application/rdf+xml")), AcceptParameters(ContentType("application/atom+xml"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml vs application/rdf+xml vs text/html with mixed q values, most preferred available +++"
    accept = "application/atom+xml;q=0.6, application/rdf+xml;q=0.9, text/html"
    server = [AcceptParameters(ContentType("application/rdf+xml")), AcceptParameters(ContentType("text/html"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ application/atom+xml;type=feed supported by server +++"
    accept = "application/atom+xml;type=feed"
    server = [AcceptParameters(ContentType("application/atom+xml;type=feed"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ image/* supported by server +++"
    accept = "image/*"
    server = [AcceptParameters(ContentType("text/plain")), AcceptParameters(ContentType("image/png")),
                AcceptParameters(ContentType("image/jpeg"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ */* supported by server +++"
    accept = "*/*"
    server = [AcceptParameters(ContentType("text/plain")), AcceptParameters(ContentType("image/png")),
                AcceptParameters(ContentType("image/jpeg"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept)
    print "+++ " + str(ap) + " +++"
    
    print "===================================="
    print "==============LANGUAGE=============="
    
    print "+++ en only +++"
    accept_language = "en"
    server = [AcceptParameters(language=Language("en"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept_language)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en vs de without q values +++"
    accept = "en, de"
    server = [AcceptParameters(language=Language("en")), AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ fr vs no with q values +++"
    accept = "fr;q=0.7, no;q=0.8"
    server = [AcceptParameters(language=Language("fr")), AcceptParameters(language=Language("no"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en vs de vs fr with mixed q values +++"
    accept = "en;q=0.6, de;q=0.9, fr"
    server = [AcceptParameters(language=Language("en")), AcceptParameters(language=Language("de")),
                AcceptParameters(language=Language("fr"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en only, unsupported by server +++"
    accept = "en"
    server = [AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en vs no vs de with mixed q values, most preferred unavailable +++"
    accept = "en;q=0.6, no;q=0.9, de"
    server = [AcceptParameters(language=Language("en")), AcceptParameters(language=Language("no"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en vs no vs de with mixed q values, most preferred available +++"
    accept = "en;q=0.6, no;q=0.9, de"
    server = [AcceptParameters(language=Language("no")), AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en-gb supported by server +++"
    accept = "en-gb"
    server = [AcceptParameters(language=Language("en-gb"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en-gb, unsupported by server +++"
    accept = "en-gb"
    server = [AcceptParameters(language=Language("en"))]
    cn = ContentNegotiator(acceptable=server, ignore_language_variants=False)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en-gb, supported by server through language variants +++"
    accept = "en-gb"
    server = [AcceptParameters(language=Language("en"))]
    cn = ContentNegotiator(acceptable=server, ignore_language_variants=True)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ en, partially supported by server +++"
    accept = "en"
    server = [AcceptParameters(language=Language("en-gb"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ * by itself +++"
    accept = "*"
    server = [AcceptParameters(language=Language("no")), AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ * with other options, primary option unsupported +++"
    accept = "en, *"
    server = [AcceptParameters(language=Language("no")), AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "+++ * with other options, primary option supported +++"
    accept = "en, *"
    server = [AcceptParameters(language=Language("en")), AcceptParameters(language=Language("de"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept_language=accept)
    print "+++ " + str(ap) + " +++"
    
    print "===================================="
    print "======LANGUAGE+CONTENT TYPE========="
    
    print "+++ content type and language specified +++"
    accept = "text/html"
    accept_lang = "en"
    server = [AcceptParameters(ContentType("text/html"), Language("en"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept, accept_language=accept_lang)
    print "+++ " + str(ap) + " +++"
    
    print "+++ 2 content types and one language specified +++"
    accept = "text/html, text/plain"
    accept_lang = "en"
    server = [AcceptParameters(ContentType("text/html"), Language("de")), AcceptParameters(ContentType("text/plain"), Language("en"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept, accept_language=accept_lang)
    print "+++ " + str(ap) + " +++"
    
    print "+++ 2 content types and 2 languages specified +++"
    accept = "text/html, text/plain"
    accept_lang = "en, de"
    server = [AcceptParameters(ContentType("text/html"), Language("de")), AcceptParameters(ContentType("text/plain"), Language("en"))]
    cn = ContentNegotiator(acceptable=server)
    ap = cn.negotiate(accept=accept, accept_language=accept_lang)
    print "+++ " + str(ap) + " +++"
    
    print "+++ 2 content types and one language specified, with weights +++"
    weights = {'content_type' : 2.0, 'language' : 1.0, 'charset' : 1.0, 'encoding' : 1.0}
    accept = "text/html, text/plain"
    accept_lang = "en"
    server = [AcceptParameters(ContentType("text/html"), Language("de")), AcceptParameters(ContentType("text/plain"), Language("en"))]
    cn = ContentNegotiator(acceptable=server, weights=weights)
    ap = cn.negotiate(accept=accept, accept_language=accept_lang)
    print "+++ " + str(ap) + " +++"