import urllib2
from utilities import _xml_to_dict, _dict_to_xml

def _request(method, url, username, password, out_data={}):
    """
        Takes an input dictionary. For PUT, sends as XML payload to the supplied URL with the given method.
        For POST, sends as POST variables.
        Returns XML result as dictionary, accounting for FeeFighters' conventions, setting datatypes

        Raises/Returns error in case of HTTPS error, <error> outer tag returned
    """

    request_debugging = 1

    req = method
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    authheader =  "Basic %s" % base64string
    req.add_header("Authorization", authheader)

    try:
        if method == "GET":
            handle = urllib2.urlopen(req)
        else:
            if method == "PUT":
                req.get_method = lambda: 'PUT'
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            req.add_header('Content-Type', 'application/xml')
            if (out_data):
                payload = _dict_to_xml(out_data)
            else:
                payload = ""

            # Build the opener, using HTTPS handler
            opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=request_debugging))
            handle = opener.open(req, payload)

        in_data = handle.read()
        handle.close()

        return _xml_to_dict(in_data)
    except urllib2.HTTPError, e:
        if request_debugging:
          print e.read()
        return {"error":{"errors":[{"context": "client", "source": "client", "key": "http_error_response_" + str(e.code) }], "info":[]}}
    except:
        return {"error":{"errors":[{"context": "client", "source": "client", "key": "unknown_response_error" }], "info":[]}}
