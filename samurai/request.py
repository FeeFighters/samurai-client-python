"""
    Python restful client.
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import urllib2
import config
import base64

class Request(urllib2.Request):
    """
    `urllib2.Request` doesn't support PUT and DELETE.
    Augmenting it to support whole REST spectrum.
    """
    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False, method=None):
       urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)
       self.method = method.upper()

    def get_method(self):
        if self.method:
            return self.method

        return urllib2.Request.get_method(self)

def fetch_url(req,
              merchant_key=config.merchant_key,
              merchant_password=config.merchant_password):
    """
    Opens a request to `req`. Handles basic auth with given `merchant_key`
    and `merchant_password`.
    """
    auth_info = base64.encodestring('%s:%s' % (merchant_key, merchant_password)).replace('\n', '')
    req.add_header("Authorization", "Basic %s" % auth_info)
    opener = urllib2.build_opener()
    try:
        res = opener.open(req).read()
    except urllib2.URLError, ex:
        res = ex.read()
    return res
