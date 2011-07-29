import urllib, urllib2, urlparse, base64, json
from datetime import datetime

from xml.dom.minidom import parseString as parseStringToXML, Node, Document

REQUESTS = {
    "transparent_redirect":     ("GET",     "https://samurai.feefighters.com/v1/payment_methods"),       # just for testing
    "fetch_payment_method":     ("GET",     "https://samurai.feefighters.com/v1/payment_methods/%s.xml"),
    "update_payment_method":    ("PUT",     "https://samurai.feefighters.com/v1/payment_methods/%s.xml"),
    "retain_payment_method":    ("POST",    "https://samurai.feefighters.com/v1/payment_methods/%s/retain.xml"),
    "redact_payment_method":    ("POST",    "https://samurai.feefighters.com/v1/payment_methods/%s/redact.xml"),
    "purchase_transaction":     ("POST",    "https://samurai.feefighters.com/v1/gateways/%s/purchase.xml"),
    "authorize_transaction":    ("POST",    "https://samurai.feefighters.com/v1/gateways/%s/authorize.xml"),
    "capture_transaction":      ("POST",    "https://samurai.feefighters.com/v1/transactions/%s/capture.xml"),
    "void_transaction":         ("POST",    "https://samurai.feefighters.com/v1/transactions/%s/void.xml"),
    "reverse_transaction":      ("POST",    "https://samurai.feefighters.com/v1/transactions/%s/credit.xml"),
    "fetch_transaction":        ("GET",     "https://samurai.feefighters.com/v1/transactions/%s.xml"),
}



def _dict_to_xml(in_data):
    doc_tagname = in_data.keys()[0]
    xml = parseStringToXML("<%s></%s>" % (doc_tagname, doc_tagname) )
    for tag_name, tag_value in in_data[doc_tagname].iteritems():
        newElement = xml.createElement(tag_name)
        newTextNode = xml.createTextNode( str(tag_value) )
        xml.documentElement.appendChild( newElement )
        newElement.appendChild( newTextNode )
    return xml.toxml()

def _xml_to_dict(xml_string):
    try:
        xml_data = parseStringToXML(xml_string)
    except: # parse error, or something
        return None # error code, perhaps

    return _xml_outer_node_to_dict(xml_data.documentElement)

# I made a mistake here. I should have made this more agnostic to tag names, and only looked at the type attribute
# and context/key in the case of messages. The consumer of the dict should take care of making it convenient
# for the consumer of the classes. Probably not worth going back at this point, though.
def _xml_outer_node_to_dict(xml_node):
    out_data = {'errors':[], 'info':[]}

    # from their API, we don't expect more than two levels of nodes.
    # doc_element > messages > message, or doc_element > datum 
    # with the exceptions of gateway_response, and an embedded payment_method
    for outer_node in (node for node in xml_node.childNodes if node.nodeType == Node.ELEMENT_NODE):
        element_type = outer_node.getAttribute('type')
        element_name = outer_node.tagName

        if element_name == 'payment_method':
            payment_method = _xml_outer_node_to_dict(outer_node)['payment_method']
            out_data['payment_method'] = payment_method
        elif element_name == 'gateway_response':
            # the structure of 'gateway_response' happens to be very similar to the document at large. level 1, data. level 2, messages
            # so we'll just call this function recursively
            gateway_response = _xml_outer_node_to_dict(outer_node)['gateway_response']
            out_data['gateway_success'] = gateway_response['success']
            for error in gateway_response['errors']:
                out_data['errors'].append( dict(error , source = "gateway") ) # it's set as a "samurai" error
            for info in gateway_response['info']:
                out_data['info'].append( dict(info , source = "gateway") ) # it's set as a "samurai" info 
        # doc_element > messages > message 
        elif element_name == 'messages':
            for message in outer_node.getElementsByTagName("message"):
                # ({'context': context, 'key': key }, samurai/gateway)
                if message.getAttribute('class') == "error":
                    out_data['errors'].append( { 'context': message.getAttribute('context'), 'key': message.getAttribute('key'), 'source': "samurai"} )
                if message.getAttribute('class') == "info":
                    out_data['info'].append( { 'context': message.getAttribute('context'), 'key': message.getAttribute('key'), 'source': "samurai"} )

        # doc_element > datum 
        else: 
            if outer_node.childNodes == []:
                out_data[element_name] = ""
            else:
                for inner_node in (node for node in outer_node.childNodes if node.nodeType == Node.TEXT_NODE):
                    if element_type == 'integer':
                        out_data[element_name] = int(inner_node.nodeValue)
                    elif element_type == 'datetime':
                        out_data[element_name] = datetime.strptime(inner_node.nodeValue, "%Y-%m-%d %H:%M:%S UTC")
                    elif element_type == 'boolean':
                        out_data[element_name] = {'true':True, 'false':False} [ inner_node.nodeValue ]
                    else:
                        out_data[element_name] = inner_node.nodeValue

    return { xml_node.tagName: out_data }

class RequestWithPut(urllib2.Request):
    use_put_method = False
    def get_method(self):
        super_method = urllib2.Request.get_method(self) # can't use super, urllib2.Request seems to be old-style class
        if self.use_put_method and super_method == 'POST':
            return 'PUT'
        else:
            return super_method

def _request(method, url, username, password, out_data={}):
    """
        Takes an input dictionary. For PUT, sends as XML payload to the supplied URL with the given method.
        For POST, sends as POST variables.
        Returns XML result as dictionary, accounting for FeeFighters' conventions, setting datatypes

        Raises/Returns error in case of HTTPS error, <error> outer tag returned
    """

    req = RequestWithPut(url)
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    authheader =  "Basic %s" % base64string
    req.add_header("Authorization", authheader)

    try:
        if method == "GET":
            handle = urllib2.urlopen(req)
        else:
            if method == "PUT":
                req.use_put_method = True
            req.add_header('Content-Type', 'application/xml')
            if (out_data):
                payload = _dict_to_xml(out_data)
            else:
                payload = ""
            handle = urllib2.urlopen(req, payload)

        in_data = handle.read()
        handle.close()

        return _xml_to_dict(in_data)
    except urllib2.HTTPError, e:
        if e.code == 404:
            return {"error":{"errors":[{"context": "client", "source": "client", "key": "error_404" }], "info":[]}}
        if e.code == 500:
            return {"error":{"errors":[{"context": "client", "source": "client", "key": "error_500" }], "info":[]}}
    except:
        return {"error":{"errors":[{"context": "client", "source": "client", "key": "unknown_response_error" }], "info":[]}}
    

class FeeFighters(object):
    "If you want to create multiple payment methods without repeating yourself with the authentication info, you can use this"

    def __init__(self, **kwargs):
        self._merchant_key = kwargs["merchant_key"]
        self._merchant_password = kwargs["merchant_password"]
        self._gateway_token = kwargs["gateway_token"]

class PaymentMethod(object):

    payment_method_token = None
    created_at = None
    updated_at = None
    custom = None
    is_retained = None
    is_redacted = None
    is_sensitive_data_valid = None
    last_four_digits = None
    card_type = None
    first_name = None
    last_name = None
    expiry_month = None
    expiry_year = None
    address_1 = None
    address_2 = None
    city = None
    state = None
    zip = None
    country = None

    _last_data = None

    field_names = ["created_at", "updated_at", "is_retained", "is_redacted", "is_sensitive_data_valid", "errors", "info", 
        "last_four_digits", "card_type", "first_name", "last_name", "expiry_month", "expiry_year", "address_1", "address_2",
        "city", "state",  "zip", "country", "custom"]

    updatable_field_names = [name for name in field_names if name not in ['custom', 'created_at', 'updated_at', 'errors', 'info']]

    def __init__(self, *args, **kwargs):
        
        if 'feefighters' in kwargs:
            self._merchant_key = kwargs['feefighters']._merchant_key
            self._merchant_password = kwargs['feefighters']._merchant_password
            self._gateway_token = kwargs['feefighters']._gateway_token
            self.payment_method_token = kwargs['payment_method_token']
        else:
            self._merchant_key = kwargs['merchant_key']
            self._merchant_password = kwargs['merchant_password']
            self._gateway_token = kwargs['gateway_token']
            self.payment_method_token = kwargs['payment_method_token']

        self._last_data = {}
        self.populated = False
        if kwargs.get("do_fetch", True):
            self.fetch() # why not? probably gonna do this anyway

        self.errors = []
        self.info = []

    def _basic_payment_method_request(self, request, payload = {}):
        "This is a basic method with no payload, and should update the payment_method data in the object's attributes"

        request = REQUESTS[request]
        in_data = _request( request[0], request[1] % self.payment_method_token, self._merchant_key, self._merchant_password, payload)

        self.errors = self.info = []

        # check if the head element is what we expect
        if "error" not in in_data and "payment_method" not in in_data:
            in_data = {'error': {'errors':[{'source': 'library', 'context': 'library', 'key': 'wrong_head_element'}], 'info':[]}}

        # check if we have all expected fields. if not, assum the whole thing is a wash.
        elif "payment_method" in in_data: # if this is a response with <error> as the head element, we won't expect these fields
            for field in self.field_names:
                if field not in in_data['payment_method']:
                    in_data = {'error': {'errors':[{'source': 'library', 'context': 'library', 'key': 'missing_fields'}], 'info':[]}}
                    break

        # handle <error> responses
        if "error" in in_data:
            self.errors = in_data['error']['errors']
            self.info = in_data['error']['info']

            self._last_data = None

            self.populated = False

            return False

        # handle <payment_method> responses
        else:
            for attr_name in self.field_names:
                setattr(self, attr_name, in_data['payment_method'][attr_name])

            if in_data['payment_method']['custom'] == "":
                in_data['payment_method']['custom'] = "{}"

            try:
                self.custom = json.loads(in_data['payment_method']['custom'])
            except:
                self.errors.append({'source': 'library', 'context': 'library', 'key':'json_decoding_error'}  )

            self._last_data = in_data['payment_method'] # so we know what changed, for update()

            self.populated = True

            return not bool(self.errors)

    def update(self):
        out_data = {'payment_method':{}}

        for attr_name in self.updatable_field_names:
            # the None would be if they hadn't fetched yet
            if self._last_data.get(attr_name, None) != getattr(self, attr_name) and getattr(self, attr_name) != None:
                out_data['payment_method'][attr_name] = getattr(self, attr_name)

        if self.custom != None and ('custom' not in self._last_data or json.loads(self._last_data['custom']) != self.custom):
            try:
                out_data['payment_method']['custom'] = json.dumps(self.custom)
            except:
                return {"error":{"errors":[{"context": "library", "source": "library", "key": "json_encoding_error" }], "info":[]}}

        return self._basic_payment_method_request("update_payment_method", out_data)
        
    def fetch(self):
        return self._basic_payment_method_request("fetch_payment_method")

    def retain(self):
        return self._basic_payment_method_request("retain_payment_method")

    def redact(self):
        return self._basic_payment_method_request("redact_payment_method")


class Transaction(object):

    def __init__(self, transaction_token = None, payment_method = None, do_fetch = True):
        if transaction_token == payment_method == None:
            raise ValueError("Must supply either transaction_token a payment_method")
        if transaction_token:   # pull up info for an existing transaction
            self.transaction_token = transaction_token 
            if do_fetch:
                self.fetch()
        else:                   # create a new transaction                              
            self.payment_method = payment_method

    def fetch():
        pass

    def purchase(self, amount, currency_code, billing_reference, customer_reference, ): # default 'USD'?
        if self.transaction_token:
            raise AlreadyPurchasedSomething

        in_data = _request('http://purchase_url', {'amount': str(amount), 'currency_code': currency_code})
        if in_data['gateway_response']['success']:
            return True
        else:
            return False

    def authorize(self, amount): # saves the txn id
        pass

    def capture(self):           # requires a txn id
        pass

    def void(self):              # requires a txn id
        pass

    def reverse(self, amount): # aka credit. requires a txn id
        pass

