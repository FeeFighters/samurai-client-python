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
        elif method == "POST":
            params = urllib.urlencode( out_data )
            handle = urllib2.urlopen(req, params)
        elif method == "PUT":
            req.use_put_method = True
            req.add_header('Content-Type', 'application/xml')
            payload = _dict_to_xml(out_data)
            handle = urllib2.urlopen(req, payload)

        in_data = handle.read()
        handle.close()

        return _xml_to_dict(in_data)
    except:
        return {"error":{"errors":[{"context": "library", "source": "library", "key": "bad_response" }], "info":[]}}
    

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

    def _basic_payment_method_request(self, request):
        "This is a basic method with no payload, and should update the payment_method data in the object's attributes"

        request = REQUESTS[request]
        in_data = _request( request[0], request[1] % self.payment_method_token, self._merchant_key, self._merchant_password)

        attr_names = ["created_at", "updated_at", "is_retained", "is_redacted", "is_sensitive_data_valid", "errors", "info", 
            "last_four_digits", "card_type", "first_name", "last_name", "expiry_month", "expiry_year", "address_1", "address_2",
            "city", "state",  "zip", "country"]

        self.errors = self.info = []

        # check if the head element is what we expect
        if "error" not in in_data and "payment_method" not in in_data:
            in_data = {'error': {'errors':[{'source': 'library', 'context': 'library', 'key': 'wrong_head_element'}], 'info':[]}}

        # check if we have all expected fields. if not, assum the whole thing is a wash.
        elif "payment_method" in in_data: # if this is a response with <error> as the head element, we won't expect these fields
            for field in attr_names:
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
            for attr_name in attr_names:
                setattr(self, attr_name, in_data['payment_method'][attr_name])

            if in_data['payment_method']['custom'] in ["", None]:
                in_data['payment_method']['custom'] = "{}"

            try:
                self.custom = json.loads(in_data['payment_method']['custom'])
            except:
                self.errors.append({'source': 'library', 'context': 'library', 'key':'json_decoding_error'}  )

            self._last_data = in_data['payment_method'] # so we know what changed, for update()

            self.populated = True

            return bool(self.errors)

    def update(self):
        out_data = {}

        # populate this dict with my data that's changed. or, if not fetched, just any data that's been set
        if self._last_data.get('updated_at', None) != self.updated_at and self.updated_at != None: # the None would be if they hadn't fetched yet
            out_data['updated_at'] = self.updated_at
            # consider data types in the opposite direction here. shouldn't really put that in _request, because those
            # conversions only need to happen here. so we need to know the datatypes ahead of time here.
        # etc
        if self._last_data.get('custom', None) != self.custom and self.custom != None: # the None would be if they hadn't fetched yet
            out_data['custom'] = tojson(self.custom)

        in_data = _request("http://update_payment_method_url", data)
        # in_data is going to be the payment method. I don't know why they would send it again. Should we save it again?
        
    def fetch(self):
        return self._basic_payment_method_request("fetch_payment_method")

    def retain(self):
        return self._basic_payment_method_request("retain_payment_method")

    def redact(self):
        return self._basic_payment_method_request("redact_payment_method")


class Transaction(object):

    def __init__(self, init_arg, fetch = True):
        if isinstance(payment_method, PaymentMethod):   # create a new transaction
            self.payment_method = init_arg
        else:                                           # pull up info for an existing transaction
            self.transaction_token = init_arg
            if fetch:
                self.fetch()

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


##############################################################
#                        Tests                               #
##############################################################

def _transparent_redirect(data):
    "for testing purposes, simulate the web form that posts directly to FeeFighters'"

    request = REQUESTS["transparent_redirect"]
    method = request[0]
    url = request[1] 

    opener = urllib2.build_opener( urllib2.HTTPCookieProcessor() )
    urllib2.install_opener( opener )
    params = urllib.urlencode( data )

    f = opener.open( url,  params )

    data = f.read()

    f.close()

    return urlparse.urlparse(f.url).netloc, urlparse.urlparse(f.url).query.split("=")[1]

def new_payment_method_token():
    # set up the payment method for a bunch of tests here
    _, payment_method_token = _transparent_redirect( initial_test_data )
    return payment_method_token

if __name__ == '__main__':
    import test_credentials

    initial_test_data = {
        "redirect_url":"http://edulender.com",
        "merchant_key":test_credentials.merchant_key,
        "custom":'{"a":"b", "c":{"d":"e"}}',
        "credit_card[first_name]":"Nobody",
        "credit_card[last_name]":"Fakerson",
        "credit_card[address_1]":"123 Fake Street",
        "credit_card[address_2]":"",
        "credit_card[city]":"Chicago",
        "credit_card[state]":"IL",
        "credit_card[zip]":"60611",
        "credit_card[card_type]": "Visa",
        "credit_card[card_number]":"0000000000000000",
        "credit_card[cvv]":"000",
        "credit_card[expiry_month]":"1",
        "credit_card[expiry_year]":"2012",
    }
       

    import unittest

    class TestTransparentRedirect(unittest.TestCase):

        def setUp(self):
            pass

        def test_transparent_redirect_error(self):
            request = REQUESTS["transparent_redirect"]

            try:
                _transparent_redirect( {} )
            except urllib2.HTTPError:
                pass
            else:
                self.fail()

        def test_transparent_redirect_success(self):
            request = REQUESTS["transparent_redirect"]

            redir_url, _ = _transparent_redirect( initial_test_data )
            self.assertEqual("www.edulender.com", redir_url)


    class TestXMLTODict(unittest.TestCase):

        def test_small_xml(self):
            in_str = "<doc><a>1</a><b>2</b></doc>"
            out_dict = _xml_to_dict(in_str)
            self.assertEqual(out_dict, {'doc': {'a': '1', 'b': '2', 'errors': [], 'info':[]}} )

        def test_data_types(self):
            in_str = "<doc><a type='integer'>1</a></doc>"
            out_dict = _xml_to_dict(in_str)
            self.assertEqual(out_dict, {'doc': {'a': 1, 'errors': [], 'info':[]}} )

            in_str = "<doc><b type='boolean'>false</b><c type='boolean'>true</c></doc>"
            out_dict = _xml_to_dict(in_str)
            self.assertEqual(out_dict, {'doc': {'b': False, 'c': True, 'errors': [], 'info':[]}} )

            in_str = "<doc><d type='datetime'>2011-04-22 17:57:56 UTC</d></doc>"
            out_dict = _xml_to_dict(in_str)
            self.assertEqual(out_dict, {'doc': {'d': datetime(2011, 4, 22, 17, 57, 56), 'errors': [], 'info':[]}} )

            in_str = "<doc><d></d></doc>"
            out_dict = _xml_to_dict(in_str)
            self.assertEqual(out_dict, {'doc': {'d': "", 'errors': [], 'info':[]}} )

        def test_messages(self):
            in_str = """
            <doc>
                <messages type='array'>
                    <message class="error" context="gateway.avs" key="country_not_supported" />
                    <message class="error" context="input.cvv" key="too_short" />
                    <message class="info" context="gateway.transaction" key="success" />
                </messages>
            </doc>
            """
            out_dict = _xml_to_dict(in_str)
            expected = {'doc': {
               'errors': [
                    {'context':'gateway.avs', 'key':'country_not_supported', 'source': "samurai"},
                    {'context':'input.cvv', 'key':'too_short', 'source': "samurai"}, 
                ],
               'info': [
                    {'context':'gateway.transaction', 'key':'success', 'source':"samurai"},
                ]
            }}

            self.assertEqual(out_dict, expected )

        def test_gateway_response(self):
            in_str = """
            <doc>
                <gateway_response>
                    <success type="boolean">false</success>
                    <messages type="array">
                        <message class="error" context="gateway.avs" key="country_not_supported" />
                        <message class="error" context="input.cvv" key="too_short" />
                    </messages>
                </gateway_response>
            </doc>
            """
            out_dict = _xml_to_dict(in_str)
            expected = {'doc': {
               'gateway_success': False,
               'errors': [
                    {'context':'gateway.avs', 'key':'country_not_supported','source': "gateway"},
                    {'context':'input.cvv', 'key':'too_short','source': "gateway"}, 
                ],
               'info': []
            }}
           
            self.assertEqual(out_dict, expected )

        def test_inner_payment_method(self):
            in_str = """
            <doc>
                <messages>
                    <message class="error" context="gateway.avs" key="country_not_supported" />
                </messages>
                <payment_method>
                    <blah type="boolean">false</blah>
                    <messages type="array">
                        <message class="error" context="input.cvv" key="too_short" />
                    </messages>
                </payment_method>
            </doc>
            """
            out_dict = _xml_to_dict(in_str)
            expected = {'doc': {
                'payment_method':{
                   'blah': False,
                   'errors': [
                        {'context':'input.cvv', 'key':'too_short', 'source': "samurai"}, 
                    ],
                   'info': []
                },
               'errors': [
                    {'context':'gateway.avs', 'key':'country_not_supported', 'source': "samurai"},
                ],
               'info': []
            }}
           
            self.assertEqual(out_dict, expected )
        

    class TestDictToXML(unittest.TestCase):
        def test_dict_to_xml(self):
            payload = {'doc':
                {'last_name': "Fakerson", 'expiry_year': 2012}
            }

            xml = _dict_to_xml(payload)
            xml = parseStringToXML(xml)

            self.assertTrue(xml.documentElement.tagName == "doc")
            self.assertTrue(xml.documentElement.getElementsByTagName('last_name')[0].childNodes[0].nodeValue == "Fakerson")
            self.assertTrue(xml.documentElement.getElementsByTagName('expiry_year')[0].childNodes[0].nodeValue == "2012")

    class TestBasicRequest(unittest.TestCase):

        def test_fetch_payment_method_error(self):
            "Test a bad GET method"
            request = REQUESTS["fetch_payment_method"]

            response = _request( request[0], request[1] % "badkey", test_credentials.merchant_key, test_credentials.merchant_password )
            self.assertTrue('error' in response)

        def test_fetch_payment_method_success(self):
            "Test a GET method"
            request = REQUESTS["fetch_payment_method"]

            payment_method_token = new_payment_method_token()

            response = _request( request[0], request[1] % payment_method_token, test_credentials.merchant_key, test_credentials.merchant_password )
            self.assertEqual(type(response), dict)

            self.assertEqual(response['payment_method']['payment_method_token'], payment_method_token)
            self.assertEqual(response['payment_method']['last_name'], "Fakerson")
            self.assertNotEqual(response['payment_method']['expiry_year'], "2012") # make sure it's an int, not string.
            self.assertEqual(response['payment_method']['expiry_year'], 2012)
            self.assertEqual(response['payment_method']['address_1'], "123 Fake Street")


        def test_update_payment_method_error(self):
            "Test a bad PUT method"
            request = REQUESTS["update_payment_method"]

            response = _request( request[0], request[1] % "badkey", test_credentials.merchant_key, test_credentials.merchant_password )
            self.assertTrue('error' in response)


        def test_update_payment_method_success(self):
            "Test a PUT method"
            request = REQUESTS["update_payment_method"]

            payload = { 'payment_method': {
               'last_name': "Actualperson",
               'address_1': "321 Real Street",
               'expiry_year': 2018,
            }}

            payment_method_token = new_payment_method_token()

            response = _request( request[0], request[1] % payment_method_token, test_credentials.merchant_key, test_credentials.merchant_password, payload )
            self.assertEqual(type(response), dict)

            self.assertEqual(response['payment_method']['last_name'], "Actualperson")
            self.assertNotEqual(response['payment_method']['expiry_year'], "2018") # make sure it's an int, not string.
            self.assertEqual(response['payment_method']['expiry_year'], 2018)
            self.assertEqual(response['payment_method']['address_1'], "321 Real Street")

            # unchanged
            self.assertEqual(response['payment_method']['payment_method_token'], payment_method_token)
            self.assertEqual(response['payment_method']['expiry_month'], 1)
            self.assertEqual(response['payment_method']['first_name'], "Nobody")

        # just a good and bad POST. no need for all methods

    
    class TestMethods(unittest.TestCase):
        "testing the actual outward facing methods of the classes"

        def setUp(self):
            self.feefighters = FeeFighters(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                gateway_token = test_credentials.gateway_token)

        def test_make_payment_method(self):
            # with FeeFighters object

            payment_method_token = new_payment_method_token()

            try:
                feefighters = FeeFighters(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                    gateway_token = test_credentials.gateway_token)
                payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
            except:
                self.fail()

            self.assertEqual(payment_method._merchant_key, test_credentials.merchant_key)
            self.assertEqual(payment_method._merchant_password, test_credentials.merchant_password)
            self.assertEqual(payment_method._gateway_token, test_credentials.gateway_token)
            self.assertEqual(payment_method.payment_method_token, payment_method_token)

            # same thing, more verbose
            try:
                payment_method = PaymentMethod(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                    gateway_token = test_credentials.gateway_token, payment_method_token = payment_method_token, do_fetch = False)
            except:
                self.fail()

            self.assertEqual(payment_method._merchant_key, test_credentials.merchant_key)
            self.assertEqual(payment_method._merchant_password, test_credentials.merchant_password)
            self.assertEqual(payment_method._gateway_token, test_credentials.gateway_token)
            self.assertEqual(payment_method.payment_method_token, payment_method_token)

        def test_do_fetch(self):
            payment_method_token = new_payment_method_token()
            payment_method_1 = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token)
            self.assertEqual(payment_method_1.first_name, "Nobody")
            payment_method_2 = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch=False)
            self.assertEqual(payment_method_2.first_name, None)


        def test_fetch(self):
            payment_method_token = new_payment_method_token()

            # payment_method_token left out, that should not be None
            attr_names = ["created_at", "updated_at", "custom", "is_retained", "is_redacted", "is_sensitive_data_valid", "last_four_digits", "card_type", "first_name", "last_name", "expiry_month", "expiry_year", "address_1", "address_2", "city", "state",  "zip", "country"]

            expected_after = {
                "payment_method_token": payment_method_token,

# may not want to bother testing for these, will have to spend time testing for approximate time
#                "created_at", 
#                "updated_at", 

                "custom": {'a':'b', 'c':{'d':'e'}},
                "is_retained": False,
                "is_redacted": False, 
                "is_sensitive_data_valid":True,
                "errors":[], 
                "info":[], #{'context':'gateway.transaction', 'key':'success', 'source':'samurai'}], 
                "last_four_digits":"0000",
                "card_type": "Visa", 
                "first_name": "Nobody", 
                "last_name": "Fakerson", 
                "expiry_month": 1, 
                "expiry_year": 2012, 
                "address_1": "123 Fake Street",
                "address_2": "", # None, 
                "city": "Chicago", 
                "state": "IL",
                "zip": "60611", 
                "country": ""
            }

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)

            for attr_name in attr_names:
                self.assertEqual(getattr(payment_method, attr_name), None)

            self.assertEqual(payment_method.errors, [])
            self.assertEqual(payment_method.info, [])

            payment_method.fetch()

            for attr_name, var_val in expected_after.iteritems():
                self.assertEqual(getattr(payment_method, attr_name), var_val)

            self.assertTrue(payment_method.populated)

        def test_bad_fetch(self):
            payment_method_token = new_payment_method_token()

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)
            payment_method.payment_method_token = "badkey"
            payment_method.fetch()

            self.assertFalse(payment_method.populated)
            self.assertEquals(payment_method.errors, [{'source':'library', 'context':'library', 'key': 'bad_response'}])

        def test_update(self):
            payment_method_token = new_payment_method_token()


        def test_redact(self):
            payment_method_token = new_payment_method_token()

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)

            self.assertFalse(payment_method.populated)

            payment_method.redact()

            self.assertTrue(payment_method.is_redacted)
            self.assertFalse(payment_method.is_retained)

            self.assertTrue(payment_method.populated)

            self.assertEqual(payment_method.zip, "60611")
            self.assertEqual(payment_method.expiry_year, 2012)

        def test_bad_redact(self):
            payment_method_token = new_payment_method_token()

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)
            payment_method.payment_method_token = "badkey"
            payment_method.redact()

            self.assertFalse(payment_method.populated)
            self.assertEquals(payment_method.errors, [{'source':'library', 'context':'library', 'key': 'bad_response'}])


        def test_retain(self):
            payment_method_token = new_payment_method_token()

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)

            self.assertFalse(payment_method.populated)

            payment_method.retain()

            self.assertTrue(payment_method.is_retained)
            self.assertFalse(payment_method.is_redacted)

            self.assertTrue(payment_method.populated)

            self.assertEqual(payment_method.zip, "60611")
            self.assertEqual(payment_method.expiry_year, 2012)

        def test_bad_retained(self):
            payment_method_token = new_payment_method_token()

            payment_method = PaymentMethod(feefighters = self.feefighters, payment_method_token = payment_method_token, do_fetch = False)
            payment_method.payment_method_token = "badkey"
            payment_method.retain()

            self.assertFalse(payment_method.populated)
            self.assertEquals(payment_method.errors, [{'source':'library', 'context':'library', 'key': 'bad_response'}])



    unittest.main()
