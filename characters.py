import unicodedata, chardet

def asciify(self, string):
    return unicodedata.normalize('NFKD', unicode(string, chardet.detect(string)['encoding'], 'ignore').encode('ascii','ignore'))