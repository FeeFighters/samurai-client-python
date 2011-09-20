import urllib, urllib2, urlparse, base64, json, string
from datetime import datetime

from xml.dom.minidom import parseString as parseStringToXML, Node, Document

REQUESTS = {
    "transparent_redirect":     ("POST",     "https://api.samurai.feefighters.com/v1/payment_methods"),       # just for testing
    "fetch_payment_method":     ("GET",     "https://api.samurai.feefighters.com/v1/payment_methods/%s.xml"),
    "update_payment_method":    ("PUT",     "https://api.samurai.feefighters.com/v1/payment_methods/%s.xml"),
    "retain_payment_method":    ("POST",    "https://api.samurai.feefighters.com/v1/payment_methods/%s/retain.xml"),
    "redact_payment_method":    ("POST",    "https://api.samurai.feefighters.com/v1/payment_methods/%s/redact.xml"),
    "purchase_transaction":     ("POST",    "https://api.samurai.feefighters.com/v1/processors/%s/purchase.xml"),
    "authorize_transaction":    ("POST",    "https://api.samurai.feefighters.com/v1/processors/%s/authorize.xml"),
    "capture_transaction":      ("POST",    "https://api.samurai.feefighters.com/v1/transactions/%s/capture.xml"),
    "void_transaction":         ("POST",    "https://api.samurai.feefighters.com/v1/transactions/%s/void.xml"),
    "credit_transaction":       ("POST",    "https://api.samurai.feefighters.com/v1/transactions/%s/credit.xml"),
    "fetch_transaction":        ("GET",     "https://api.samurai.feefighters.com/v1/transactions/%s.xml"),
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
    # with the exceptions of processor_response, and an embedded payment_method
    for outer_node in (node for node in xml_node.childNodes if node.nodeType == Node.ELEMENT_NODE):
        element_type = outer_node.getAttribute('type')
        element_name = outer_node.tagName

        if element_name == 'payment_method':
            payment_method = _xml_outer_node_to_dict(outer_node)['payment_method']
            out_data['payment_method'] = payment_method
        elif element_name == 'processor_response':
            # the structure of 'processor_response' happens to be very similar to the document at large. level 1, data. level 2, messages
            # so we'll just call this function recursively
            processor_response = _xml_outer_node_to_dict(outer_node)['processor_response']
            out_data['processor_success'] = processor_response.get('success', False)
            for error in processor_response['errors']:
                out_data['errors'].append( dict(error , source = "processor") ) # it's set as a "samurai" error
            for info in processor_response['info']:
                out_data['info'].append( dict(info , source = "processor") ) # it's set as a "samurai" info 
        # doc_element > messages > message 
        elif element_name == 'messages':
            for message in outer_node.getElementsByTagName("message"):
                # ({'context': context, 'key': key }, samurai/processor)
                if message.getAttribute('subclass') == "error":
                    out_data['errors'].append( { 'context': message.getAttribute('context'), 'key': message.getAttribute('key'), 'source': "samurai"} )
                if message.getAttribute('subclass') == "info":
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

    request_debugging = 1

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

            # Build the opener, using HTTPS handler
            opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=request_debugging))
            handle = opener.open(req, payload)

            # handle = urllib2.urlopen(req, payload)

        in_data = handle.read()
        handle.close()

        return _xml_to_dict(in_data)
    except urllib2.HTTPError, e:
        if request_debugging:
          print e.read()
        return {"error":{"errors":[{"context": "client", "source": "client", "key": "http_error_response_" + str(e.code) }], "info":[]}}
    except:
        return {"error":{"errors":[{"context": "client", "source": "client", "key": "unknown_response_error" }], "info":[]}}
    

class FeeFighters(object):
    "If you want to create multiple payment methods without repeating yourself with the authentication info, you can use this"

    def __init__(self, **kwargs):
        self.merchant_key = kwargs["merchant_key"]
        self.merchant_password = kwargs["merchant_password"]

class RemoteObject(object):

    def _remote_object_request(self, request_name, url_parameter, payload = {}, field_names = None):
        "This is a method that handles all requests, and should update the object's attributes with the new data"

        if field_names == None:
            field_names = self.field_names
    
        request = REQUESTS[request_name]
        in_data = _request( request[0], request[1] % url_parameter, self._merchant_key, self._merchant_password, payload)

        return self._load_data_from_dict(in_data, field_names)

    def _load_data_from_dict(self, in_data, field_names): 

        self.errors = self.info = []

        # check if the head element is what we expect
        if "error" not in in_data and self.head_xml_element_name not in in_data:
            in_data = {'error': {'errors':[{'source': 'client', 'context': 'client', 'key': 'wrong_head_element'}], 'info':[]}}

        # check if we have all expected fields. if not, assume the whole thing is a wash.
        elif self.head_xml_element_name in in_data: # if this is a response with <error> as the head element, we won't expect these fields
            for field in field_names:
                if field not in in_data[self.head_xml_element_name]:
                    in_data = {'error': {'errors':[{'source': 'client', 'context': 'client', 'key': 'missing_fields'}], 'info':[]}}
                    break

        # handle <error> responses
        if "error" in in_data:
            self.errors = in_data['error']['errors']
            self.info = in_data['error']['info']

            self._last_data = None

            self.populated = False

            return False

        # handle responses with the expected head element
        else:
            for field in field_names:
                setattr(self, field, in_data[self.head_xml_element_name][field])

            for field in self.json_field_names:
                if in_data[self.head_xml_element_name][field] == "":
                    in_data[self.head_xml_element_name][field] = "{}"

                try:
                    setattr(self, field, json.loads(in_data[self.head_xml_element_name][field]))
                except:
                    self.errors.append({'source': 'client', 'context': 'client', 'key':'json_decoding_error'}  )

            self._last_data = in_data[self.head_xml_element_name] # so we know what changed, for update()

            self.populated = True

            return not bool(self.errors)

    def as_dict(self):
        fields_as_dict = {}
        for field_name in self.field_names:
            fields_as_dict[field_name] = getattr(self, field_name)
        return fields_as_dict 

class PaymentMethod(RemoteObject):

    payment_method_token = None
    created_at = None
    updated_at = None
    custom = {}
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

    json_field_names = ["custom"]

    updatable_field_names = [name for name in field_names if name not in ['custom', 'created_at', 'updated_at', 'errors', 'info']]

    head_xml_element_name = "payment_method"

    def __init__(self, *args, **kwargs):
        if 'feefighters' in kwargs and 'payment_method_initial' in kwargs:
            raise ValueError("Can't supply both feefighters and payment_method_initial")
        
        if 'payment_method_initial' in kwargs:
            # we want to grab the token here, since this payment method will probably be coming back from a transaction
            self._load_data_from_dict(kwargs['payment_method_initial'], self.field_names + ["payment_method_token"])
            self._merchant_key = kwargs['merchant_key']
            self._merchant_password = kwargs['merchant_password']
        elif 'feefighters' in kwargs:
            self._merchant_key = kwargs['feefighters'].merchant_key
            self._merchant_password = kwargs['feefighters'].merchant_password
            self.payment_method_token = kwargs['payment_method_token']
        else:
            self._merchant_key = kwargs['merchant_key']
            self._merchant_password = kwargs['merchant_password']
            self.payment_method_token = kwargs['payment_method_token']

        self._last_data = {}
        self.populated = False
        if kwargs.get("do_fetch", True):
            self.fetch() # why not? probably gonna do this anyway

        self.errors = []
        self.info = []

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
                self.errors.append({"error":{"errors":[{"context": "client", "source": "client", "key": "json_encoding_error" }], "info":[]}})
                return False

        return self._remote_object_request("update_payment_method", self.payment_method_token, out_data)
        
    def fetch(self):
        return self._remote_object_request("fetch_payment_method", self.payment_method_token)

    def retain(self):
        return self._remote_object_request("retain_payment_method", self.payment_method_token)

    def redact(self):
        return self._remote_object_request("redact_payment_method", self.payment_method_token)

class Transaction(RemoteObject):

    reference_id        = None
    transaction_token   = None
    created_at          = None
    descriptor          = {}
    custom              = {}
    transaction_type    = None
    amount              = None
    currency_code       = None
    processor_success     = None
    payment_method      = None

    field_names = ["reference_id", "created_at", "descriptor", "custom", "transaction_type", "amount",
                    "currency_code", "processor_success", "payment_method", "info", "errors", "transaction_token"]

    json_field_names = ["custom", "descriptor"]

    head_xml_element_name = "transaction"

    def __init__(self, **kwargs):
        self.populated = False
        if kwargs.get('reference_id', None) == kwargs.get('payment_method', None) == None:
            raise ValueError("Must supply either a reference_id or a payment_method")

        if 'feefighters' in kwargs:
            self._merchant_key = kwargs['feefighters'].merchant_key
            self._merchant_password = kwargs['feefighters'].merchant_password
        else:
            self._merchant_key = kwargs['merchant_key']
            self._merchant_password = kwargs['merchant_password']

        if kwargs.get('reference_id', None):   # pull up info for an existing transaction
            self.reference_id = kwargs.get('reference_id', None)
            if kwargs.get('do_fetch', True):
                self.fetch()
        else:                   # create a new transaction                              
            self.payment_method = kwargs.get('payment_method', None)
            if kwargs.get('do_fetch', True):
                self.payment_method.fetch()
            self.processor_token = kwargs['processor_token'] # can be got from the transaction via fetch, if a reference_id is there

        self.errors = []
        self.info = []

    def _transaction_request(self, request_name, url_parameter, payload = {}, field_names = None):
        success = True
        if self._remote_object_request(request_name, url_parameter, payload, field_names):
            if type(self.payment_method) == dict:
                self.payment_method = PaymentMethod(payment_method_initial = {'payment_method':self.payment_method}, merchant_key = self._merchant_key,
                    merchant_password = self._merchant_password)
            if self.payment_method.errors:
                self.errors.append({"error":{"errors":[{"context": "client", "source": "client", "key": "errors_in_returned_payment_method" }], "info":[]}})
                success = False
        else:
            if type(self.payment_method) == dict:
                self.payment_method = PaymentMethod(payment_method_initial = {'payment_method':self.payment_method}, merchant_key = self._merchant_key,
                    merchant_password = self._merchant_password)
            success = False

        if self.transaction_type:
            self.transaction_type = self.transaction_type.lower() # so we don't get tripped up remembering "Purchase" vs "purchase"
        return success

    def _add_json_fields(self, out_data):
        for field in ['custom', 'descriptor']:
            if getattr(self, field) != None:
                try:
                    out_data['transaction'][field] = json.dumps(getattr(self, field))
                except:
                    self.errors.append({"error":{"errors":[{"context": "client", "source": "client", "key": "json_encoding_error" }], "info":[]}})
                    return False
            else:
                out_data['transaction'][field] = "{}"

        return True


    def purchase(self, amount, currency_code, billing_reference, customer_reference): # default 'USD'?
        if self.reference_id:
            self.errors = [{"context": "client", "source": "client", "key": "attempted_purchase_on_existing_transaction" }]
            return False

        out_data = {'transaction':{
            'type':'purchase',
            'amount': str(amount),
            'currency_code': currency_code,
            'payment_method_token': self.payment_method.payment_method_token,
            'billing_reference':billing_reference,
            'customer_reference':customer_reference,
        }}

        if not self._add_json_fields(out_data):
            return False

        return self._transaction_request("purchase_transaction", self.processor_token, out_data)

    def authorize(self, amount, currency_code, billing_reference, customer_reference): # default 'USD'?
        if self.reference_id:
            return {"error":{"errors":[{"context": "client", "source": "client", "key": "attempted_authorize_on_existing_transaction" }], "info":[]}}

        out_data = {'transaction':{
            'type':'authorize',
            'amount': str(amount),
            'currency_code': currency_code,
            'payment_method_token': self.payment_method.payment_method_token,
            'billing_reference':billing_reference,
            'customer_reference':customer_reference,
        }}

        if not self._add_json_fields(out_data):
            return False

        return self._transaction_request("authorize_transaction", self.processor_token, out_data)

    def capture(self, amount): # default 'USD'?
        # in case we're rebuilding this transaction from a reference_id, and they didn't want to fetch initially
        if self.transaction_token == None:
            self.fetch()

        new_transaction = Transaction(merchant_key = self._merchant_key, merchant_password = self._merchant_password, 
                                      reference_id=self.reference_id, do_fetch= False)
        new_transaction.transaction_token = self.transaction_token

        out_data = {'transaction':{
            'amount': str(amount),
        }}

        new_transaction._transaction_request("capture_transaction", new_transaction.transaction_token, out_data)

        return new_transaction

    def void(self):
        # in case we're rebuilding this transaction from a reference_id, and they didn't want to fetch initially
        if self.transaction_token == None:
            self.fetch()

        new_transaction = Transaction(merchant_key = self._merchant_key, merchant_password = self._merchant_password, 
                                      reference_id=self.reference_id, do_fetch= False)
        new_transaction.transaction_token = self.transaction_token

        new_transaction._transaction_request("void_transaction", new_transaction.transaction_token)

        return new_transaction

    def credit(self, amount):
        # in case we're rebuilding this transaction from a reference_id, and they didn't want to fetch initially
        if self.transaction_token == None:
            self.fetch()

        out_data = {'transaction':{
            'amount': str(amount),
        }}

        new_transaction = Transaction(merchant_key = self._merchant_key, merchant_password = self._merchant_password, 
                                      reference_id=self.reference_id, do_fetch= False)
        new_transaction.transaction_token = self.transaction_token

        new_transaction._transaction_request("credit_transaction", new_transaction.transaction_token, out_data)

        return new_transaction

    def fetch(self):
        return self._transaction_request("fetch_transaction", self.reference_id, {},list(set(self.field_names) - set(['reference_id'])))
