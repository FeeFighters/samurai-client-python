"""
    Python restful client.
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import urllib2

class Request(urllib2.Request):
    """
    `urllib2.Request` doesn't support PUT and DELETE.
    Augmenting it to support whole REST spectrum.
    """
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'

    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False, method=None):
       urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)
       self.method = method

    def get_method(self):
        if self.method:
            return self.method

        return urllib2.Request.get_method(self)

def fetch_url(req):
    opener = urllib2.build_opener(urllib2.HttpHandler)
    return opener.open(req)
