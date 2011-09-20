import test_credentials
from core import *
from core import _xml_to_dict, _dict_to_xml, _request
import time

# We need a handler that doesn't follow redirects, 
# so we can grab the Location header and return it
class NoRedirectHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return headers['Location']
    http_error_301 = http_error_303 = http_error_307 = http_error_302


def _transparent_redirect(data):
    "for testing purposes, simulate the web form that posts directly to FeeFighters'"

    request = REQUESTS["transparent_redirect"]
    method = request[0]
    url = request[1] 

    # URL-Encode the data
    params = urllib.urlencode(data)

    # Setup a HTTPS handler with debugging enabled (or not)
    request_debugging = 0

    # Build the opener, using our special NoRedirect handler + HTTPS handler
    opener = urllib2.build_opener(NoRedirectHTTPRedirectHandler, urllib2.HTTPSHandler(debuglevel=request_debugging))
    # make the request, and just store the result in data 
    # because our NoRedirect handler simply returns the Location string
    data = opener.open(url, params)

    # Parse the Location redirect string into its parts, and return them
    return urlparse.urlparse(data).netloc, urlparse.urlparse(data).query.split("=")[1]

def _new_payment_method_token():
    # set up the payment method for a bunch of tests here
    _, payment_method_token = _transparent_redirect( initial_test_data )
    return payment_method_token

initial_test_data = {
    "redirect_url":"http://localhost",
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
    "credit_card[card_number]":"4222222222222",
    "credit_card[cvv]":"000",
    "credit_card[expiry_month]":"1",
    "credit_card[expiry_year]":"2012",
    "sandbox":"true"
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
        self.assertEqual("localhost", redir_url)


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
                <message subclass="error" context="processor.avs" key="country_not_supported" />
                <message subclass="error" context="input.cvv" key="too_short" />
                <message subclass="info" context="processor.transaction" key="success" />
            </messages>
        </doc>
        """
        out_dict = _xml_to_dict(in_str)
        expected = {'doc': {
           'errors': [
                {'context':'processor.avs', 'key':'country_not_supported', 'source': "samurai"},
                {'context':'input.cvv', 'key':'too_short', 'source': "samurai"}, 
            ],
           'info': [
                {'context':'processor.transaction', 'key':'success', 'source':"samurai"},
            ]
        }}

        self.assertEqual(out_dict, expected )

    def test_processor_response(self):
        in_str = """
        <doc>
            <processor_response>
                <success type="boolean">false</success>
                <messages type="array">
                    <message subclass="error" context="processor.avs" key="country_not_supported" />
                    <message subclass="error" context="input.cvv" key="too_short" />
                </messages>
            </processor_response>
        </doc>
        """
        out_dict = _xml_to_dict(in_str)
        expected = {'doc': {
           'processor_success': False,
           'errors': [
                {'context':'processor.avs', 'key':'country_not_supported','source': "processor"},
                {'context':'input.cvv', 'key':'too_short','source': "processor"}, 
            ],
           'info': []
        }}
       
        self.assertEqual(out_dict, expected )

    def test_inner_payment_method(self):
        in_str = """
        <doc>
            <messages>
                <message subclass="error" context="processor.avs" key="country_not_supported" />
            </messages>
            <payment_method>
                <blah type="boolean">false</blah>
                <messages type="array">
                    <message subclass="error" context="input.cvv" key="too_short" />
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
                {'context':'processor.avs', 'key':'country_not_supported', 'source': "samurai"},
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

        payment_method_token = _new_payment_method_token()

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

        payment_method_token = _new_payment_method_token()

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



feefighters = FeeFighters(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
    processor_token = test_credentials.processor_token)

class TestPaymentMethodMethods(unittest.TestCase):
    "testing the actual outward facing methods of the classes"

    def test_make_payment_method(self):
        # with FeeFighters object

        payment_method_token = _new_payment_method_token()

        try:
            payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(payment_method._merchant_key, test_credentials.merchant_key)
        self.assertEqual(payment_method._merchant_password, test_credentials.merchant_password)
        self.assertEqual(payment_method.payment_method_token, payment_method_token)

        # same thing, more verbose
        try:
            payment_method = PaymentMethod(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                processor_token = test_credentials.processor_token, payment_method_token = payment_method_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(payment_method._merchant_key, test_credentials.merchant_key)
        self.assertEqual(payment_method._merchant_password, test_credentials.merchant_password)
        self.assertEqual(payment_method.payment_method_token, payment_method_token)

    def test_do_fetch(self):
        payment_method_token = _new_payment_method_token()
        payment_method_1 = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token)
        self.assertEqual(payment_method_1.first_name, "Nobody")
        payment_method_2 = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch=False)
        self.assertEqual(payment_method_2.first_name, None)


    def test_fetch(self):
        payment_method_token = _new_payment_method_token()

        # token left out, that one should never be None
        expected_none = ["created_at", "updated_at", "is_retained", "is_redacted", "is_sensitive_data_valid",
                         "last_four_digits", "card_type", "first_name", "last_name", "expiry_month", "expiry_year",
                         "address_1", "address_2", "city", "state",  "zip", "country"]

        expected_after = {
            "payment_method_token": payment_method_token,
            "custom": {'a':'b', 'c':{'d':'e'}},
            "is_retained": False,
            "is_redacted": False, 
            "is_sensitive_data_valid":True,
            "errors":[], 
            "info":[], #{'context':'processor.transaction', 'key':'success', 'source':'samurai'}], 
            "last_four_digits":"2222",
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

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        for attr_name in expected_none:
            self.assertEqual(getattr(payment_method, attr_name), None)

        self.assertEqual(payment_method.errors, [])
        self.assertEqual(payment_method.info, [])
        self.assertEqual(payment_method.custom, {})

        payment_method.fetch()

        for attr_name, var_val in expected_after.iteritems():
            self.assertEqual(getattr(payment_method, attr_name), var_val)

        self.assertEqual(type(payment_method.created_at), datetime)
        self.assertEqual(type(payment_method.updated_at), datetime)

        self.assertTrue(payment_method.populated)

    def test_bad_fetch(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method.payment_method_token = "badkey"
        payment_method.fetch()

        self.assertFalse(payment_method.populated)
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'http_error_response_404'}])

    def test_update(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method_check = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token)

        expected_before = {
            "payment_method_token": payment_method_token,
            "custom": {'a':'b', 'c':{'d':'e'}},
            "is_retained": False,
            "is_redacted": False, 
            "is_sensitive_data_valid":True,
            "errors":[], 
            "info":[], #{'context':'processor.transaction', 'key':'success', 'source':'samurai'}], 
            "last_four_digits":"2222",
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

        expected_after = {
            "payment_method_token": payment_method_token,
            "custom": {'x':'y', 'z':['a', 'b', 'c']},
            "is_retained": False,
            "is_redacted": False, 
            "is_sensitive_data_valid":True,
            "errors":[], 
            "info":[], #{'context':'processor.transaction', 'key':'success', 'source':'samurai'}], 
            "last_four_digits":"2222",
            "card_type": "Mastercard", 
            "first_name": "Nobody", 
            "last_name": "Fakerson", 
            "expiry_month": 1, 
            "expiry_year": 2018, 
            "address_1": "123 Fake Street",
            "address_2": "", # None, 
            "city": "Chicago", 
            "state": "IL",
            "zip": "60611", 
            "country": ""
        }

        payment_method.card_type = "Mastercard"
        payment_method.expiry_year = 2018
        payment_method.custom = {'x':'y', 'z':['a', 'b', 'c']}

        for attr_name, var_val in expected_before.iteritems():
            self.assertEqual(getattr(payment_method_check, attr_name), var_val)

        payment_method.update()

        payment_method_check.fetch()

        for attr_name, var_val in expected_after.iteritems():
            self.assertEqual(getattr(payment_method_check, attr_name), var_val)

    def test_update_before_or_after_fetch(self):
        "Tests that you can update items in a PaymentMethod before or after a fetch. Those are handled slightly differently."

        # update before fetch first
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method_check = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        payment_method.expiry_year = 2020
        payment_method.custom = {'a':'b'} # handled somewhat differently, better test it

        payment_method.update()
        payment_method_check.fetch()

        self.assertEquals(payment_method_check.expiry_year, 2020)
        self.assertEquals(payment_method_check.custom, {'a':'b'})

        # update after fetch next
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method_check = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        payment_method.fetch()

        payment_method.expiry_year = 2020
        payment_method.custom = {'a':'b'} # handled somewhat differently, better test it

        payment_method.update()
        payment_method_check.fetch()

        self.assertEquals(payment_method_check.expiry_year, 2020)
        self.assertEquals(payment_method_check.custom, {'a':'b'})


    def test_redact(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        self.assertFalse(payment_method.populated)

        payment_method.redact()

        self.assertTrue(payment_method.is_redacted)
        self.assertFalse(payment_method.is_retained)

        self.assertTrue(payment_method.populated)

        self.assertEqual(payment_method.zip, "60611")
        self.assertEqual(payment_method.expiry_year, 2012)

    def test_bad_redact(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method.payment_method_token = "badkey"
        payment_method.redact()

        self.assertFalse(payment_method.populated)
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'http_error_response_404'}])


    def test_retain(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        self.assertFalse(payment_method.populated)

        payment_method.retain()

        self.assertTrue(payment_method.is_retained)
        self.assertFalse(payment_method.is_redacted)

        self.assertTrue(payment_method.populated)

        self.assertEqual(payment_method.zip, "60611")
        self.assertEqual(payment_method.expiry_year, 2012)

    def test_bad_retained(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        payment_method.payment_method_token = "badkey"
        payment_method.retain()

        self.assertFalse(payment_method.populated)
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'http_error_response_404'}])

class TestTransactionMethods(unittest.TestCase):

    def test_make_transaction_with_payment_method(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        try:
            transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(type(transaction.payment_method), PaymentMethod)
        self.assertEqual(transaction.payment_method.payment_method_token, payment_method_token)
        self.assertEqual(transaction.payment_method.first_name, None)  # do_fetch being False

        try:
            Transaction(feefighters = feefighters, processor_token = test_credentials.processor_token, do_fetch = False)
        except ValueError:
            pass
        except:
            self.fail()
        else:
            self.fail()

    def test_make_transaction_credentials(self):
        # with FeeFighters object

        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        try:
            transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(transaction._merchant_key, test_credentials.merchant_key)
        self.assertEqual(transaction._merchant_password, test_credentials.merchant_password)
        self.assertEqual(transaction.processor_token, test_credentials.processor_token)

        # same thing, more verbose
        try:
            transaction = Transaction(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                processor_token = test_credentials.processor_token, payment_method = payment_method, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(transaction._merchant_key, test_credentials.merchant_key)
        self.assertEqual(transaction._merchant_password, test_credentials.merchant_password)
        self.assertEqual(transaction.processor_token, test_credentials.processor_token)

    def test_purchase(self):
        payment_method_token = _new_payment_method_token()

        expected_none = ["reference_id", "transaction_token", "created_at", "transaction_type", "amount", "currency_code", "processor_success" ]

        expected_after = {
            "custom": {'a':'b'},
            "descriptor": {'c':'d'},
            "transaction_type":"purchase",
            "amount":"20.5",
            "currency_code":"USD",
#            "processor_token":test_credentials.processor_token, # why would we even get this back? I'd rather not update it, it shouldn't change.
            "processor_success": True,
            "errors":[],
        }

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        for attr_name in expected_none:
            self.assertEqual(getattr(transaction, attr_name), None, attr_name + " not None")

        self.assertEqual(transaction.descriptor, {})
        self.assertEqual(transaction.custom, {})

        self.assertEqual(transaction.errors, [])
        self.assertEqual(transaction.info, [])

        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        for attr_name, var_val in expected_after.iteritems():
            self.assertEqual(getattr(transaction, attr_name), var_val)

        expected_info = {'source':'processor', 'context':'processor.transaction', 'key':'success'}
        self.assertTrue(expected_info in transaction.info, str(expected_info) + " not in " + str(transaction.info))

        # harder-to-test-for attributes
        self.assertEqual(type(transaction.created_at), datetime)
        self.assertEqual(type(transaction.reference_id), unicode)
        self.assertNotEqual(transaction.reference_id, "")
        self.assertEqual(type(transaction.transaction_token), unicode)
        self.assertNotEqual(transaction.transaction_token, "")

        self.assertEqual(type(transaction.payment_method), PaymentMethod)
        self.assertEqual(transaction.payment_method.payment_method_token, payment_method_token)
        self.assertEqual(transaction.payment_method.first_name, "Nobody")

        self.assertTrue(transaction.populated)

    def test_bad_purchase(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}
        transaction.payment_method.payment_method_token = "bad_token" # just to throw a wrench in the works

        self.assertEqual(transaction.purchase(20.5, "USD", "12345", "321"), False)

        self.assertTrue(bool(transaction.errors))
        self.assertEqual(type(transaction.payment_method), PaymentMethod)


    def test_bad_purchase_duplicate(self): # this was based on a particular error I found.
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))


        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}
        self.assertEqual(transaction.purchase(20.5, "USD", billing_reference, customer_reference), True)
        self.assertEqual(type(transaction.payment_method), PaymentMethod) # make sure we don't get dicts in the payment method after bad purchases 

        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}
        self.assertEqual(transaction.purchase(20.5, "USD", billing_reference, customer_reference), False)
        self.assertEqual(type(transaction.payment_method), PaymentMethod) # make sure we don't get dicts in the payment method after bad purchases 

        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}
        self.assertEqual(transaction.purchase(20.5, "USD", billing_reference + "0", customer_reference + "0"), True)
        self.assertEqual(type(transaction.payment_method), PaymentMethod) # make sure we don't get dicts in the payment method after bad purchases 

    def test_fetch(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        transaction_test = Transaction(feefighters = feefighters, reference_id = transaction.reference_id, do_fetch= False)

        for field_name in set(Transaction.field_names) - set(['info', 'errors', 'reference_id', 'descriptor', 'custom']):
            self.assertEqual(getattr(transaction_test, field_name), None, field_name + " not None: " + str(getattr(transaction_test, field_name)))

        self.assertEqual(transaction_test.descriptor, {})
        self.assertEqual(transaction_test.custom, {})

        self.assertTrue(transaction_test.fetch(), transaction_test.errors)

        self.assertEquals(transaction_test.errors, [])
        self.assertEquals(transaction_test.payment_method.payment_method_token, transaction.payment_method.payment_method_token)
        self.assertEquals(transaction_test.payment_method.first_name, transaction.payment_method.first_name)
        self.assertEquals(transaction_test.payment_method.expiry_year, transaction.payment_method.expiry_year)
        self.assertEquals(transaction_test.payment_method.updated_at, transaction.payment_method.updated_at)

        for field_name in set(Transaction.field_names) - set(['errors', 'info', 'payment_method']):
            self.assertEqual(getattr(transaction_test, field_name), getattr(transaction, field_name)),

    def test_do_fetch(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token)

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        transaction_1 = Transaction(feefighters = feefighters, reference_id = transaction.reference_id)
        self.assertEqual(transaction_1.amount, "20.5")
        transaction_2 = Transaction(feefighters = feefighters, reference_id = transaction.reference_id, do_fetch=False)
        self.assertEqual(transaction_2.amount, None)


    def test_authorize_capture(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        # basic checks
        def check(t, t_type):
            self.assertEqual(type(t.created_at), datetime)
            self.assertEqual(type(t.reference_id), unicode)
            self.assertNotEqual(t.reference_id, "")
            self.assertEqual(type(t.transaction_token), unicode)
            self.assertNotEqual(t.transaction_token, "")

            self.assertEqual(type(t.payment_method), PaymentMethod)
            self.assertEqual(t.payment_method.payment_method_token, payment_method_token)
            self.assertEqual(t.payment_method.first_name, "Nobody")

            self.assertTrue(t.populated)

            expected_info = {'source':'processor', 'context':'processor.transaction', 'key':'success'}
            self.assertTrue(expected_info in transaction.info, str(expected_info) + " not in " + str(transaction.info))
            self.assertEqual(t.errors, [])

            self.assertEqual(t.transaction_type, t_type, t.errors)

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))



        # First, make an authorize transaction
        self.assertTrue(transaction.authorize(20.5, "USD", billing_reference, customer_reference), transaction.errors)
        check(transaction, "authorize")
        ref_id = transaction.reference_id

        # Now try to capture it
        capture_transaction = transaction.capture(20.5)
        check(capture_transaction, "capture")

        # Now re-fetch the first transaction
        self.assertTrue(transaction.fetch())
        check(transaction, "authorize") # confirm that it is still an "authorize" transaction
        self.assertNotEqual(transaction.reference_id, capture_transaction.reference_id) # and that the ref IDs is different from the other txn
        self.assertEqual(ref_id, transaction.reference_id) # but hasn't changed from the fetch

    def test_authorize_capture_from_fetched(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        # basic checks
        def check(t, t_type):
            self.assertEqual(type(t.created_at), datetime)
            self.assertEqual(type(t.reference_id), unicode)
            self.assertNotEqual(t.reference_id, "")
            self.assertEqual(type(t.transaction_token), unicode)
            self.assertNotEqual(t.transaction_token, "")

            self.assertEqual(type(t.payment_method), PaymentMethod)
            self.assertEqual(t.payment_method.payment_method_token, payment_method_token)
            self.assertEqual(t.payment_method.first_name, "Nobody")
            self.assertEqual(t.errors, [])

            self.assertTrue(t.populated)

            expected_info = {'source':'processor', 'context':'processor.transaction', 'key':'success'}
            self.assertTrue(expected_info in transaction.info, str(expected_info) + " not in " + str(transaction.info))

            self.assertEqual(t.transaction_type, t_type, t.errors)

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))



        self.assertTrue(transaction.authorize(20.5, "USD", "x" + billing_reference, "x" + customer_reference), transaction.errors)

        # Fetch a copy of the authorized transaction
        transaction_to_capture = Transaction(feefighters = feefighters, reference_id = transaction.reference_id)

        # Capture, confirm that the ref_id and txn_type changed during the capture
        check(transaction_to_capture, "authorize")
        capture_transaction = transaction_to_capture.capture(20.5)
        self.assertNotEqual(transaction_to_capture.reference_id, capture_transaction.reference_id) 
        check(capture_transaction, "capture")

        # Re-fetch the original transaction, make sure nothing changed
        self.assertEqual(transaction.transaction_type, "authorize")
        ref_id = transaction.reference_id
        transaction.fetch()
        self.assertEqual(transaction.transaction_type, "authorize")
        self.assertEqual(ref_id, transaction.reference_id) 

    def test_void(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))


        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        self.assertEquals(transaction.transaction_type, "purchase")
        void_transaction = transaction.void()
        self.assertEqual(void_transaction.errors, [])
        self.assertEquals(void_transaction.transaction_type, "void")

        # from authorize

        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)

        self.assertTrue(transaction.authorize(20.5, "USD", billing_reference, customer_reference), transaction.errors)
        capture_transaction = transaction.capture(20.5)

        self.assertEqual(capture_transaction.errors, [])
        self.assertEquals(capture_transaction.transaction_type, "capture")

        void_transaction = capture_transaction.void()

        self.assertEqual(void_transaction.errors, [])
        self.assertEquals(void_transaction.transaction_type, "void")


    def test_credit(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))


        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        self.assertEquals(transaction.transaction_type, "purchase")
        credit_transaction = transaction.credit(10)

        self.assertEquals(credit_transaction.errors, [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}])
        self.assertEquals(credit_transaction.transaction_type, "credit")

        self.assertEquals(credit_transaction.amount, "10.0")

        self.assertTrue(transaction.fetch())
        self.assertEquals(transaction.amount, "20.5")
        self.assertEquals(transaction.errors, [])


    def test_use_unfetched_transaction(self):
        "Trying the sequence of events with all copied transactions, without calling fetch explicitly"

        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        # new transaction
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        # copy ref_id, don't fetch, void
        transaction = Transaction(feefighters = feefighters, reference_id=transaction.reference_id, do_fetch= False)
        void_transaction = transaction.void()
        self.assertEqual(void_transaction.errors, [])
        self.assertEqual(void_transaction.transaction_type, "void")

        ###
        # another sequence
        ###

        # new transaction
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, processor_token = test_credentials.processor_token, do_fetch= False)
        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        # authorize
        self.assertTrue(transaction.authorize(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        # copy ref_id, don't fetch, capture
        transaction = Transaction(feefighters = feefighters, reference_id=transaction.reference_id, do_fetch= False)
        capture_transaction = transaction.capture(20.5)
        self.assertEquals(capture_transaction.errors, [])
        self.assertEqual(capture_transaction.transaction_type, "capture")

        # copy ref_id, don't fetch, credit 
        capture_transaction = Transaction(feefighters = feefighters, reference_id=capture_transaction.reference_id, do_fetch= False)
        credit_transaction = capture_transaction.credit(10)
        self.assertEqual(credit_transaction.errors, [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}])
        self.assertEqual(credit_transaction.transaction_type, "credit")




class TestDjangoModels(unittest.TestCase):

    def test_sequence_not_through_db_1(self):
        from models import PaymentMethod, Transaction, User
        import time

        user, _ = User.objects.get_or_create(username="unit_test_user")
        PaymentMethod.objects.create(payment_method_token = _new_payment_method_token(), user = user)

        ### purchase void 

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        Transaction.objects.all().delete()
        pm = PaymentMethod.objects.all()[0]
        t = Transaction(payment_method = pm, processor_token = test_credentials.processor_token)
        t.purchase(20, "USD", billing_reference, customer_reference)
        self.assertTrue( t.errors == [] )
        self.assertTrue( t.amount == "20.0" )
        self.assertTrue( t.transaction_type == "purchase" )
        self.assertTrue( Transaction.objects.all().count() == 1 )
        self.assertTrue( t.fetch() )

        void_txn = t.void()
        self.assertTrue( void_txn.errors == [] )
        self.assertTrue( void_txn.transaction_type == "void" )
        self.assertTrue( Transaction.objects.all().count() == 2 )
        self.assertTrue( void_txn.fetch() )

        # check that stuff is in DB

        pt_db = Transaction.objects.get(transaction_type = "purchase", transaction_token = t.transaction_token)
        self.assertTrue( pt_db.amount == "20.0" )
        self.assertTrue( pt_db.fetch() )
        self.assertTrue( pt_db.amount == "20.0" )

        vt_db = Transaction.objects.get(transaction_type = "void", transaction_token = t.transaction_token)
        self.assertTrue( pt_db.amount == "20.0" )
        self.assertTrue( vt_db.fetch() )
        self.assertTrue( pt_db.amount == "20.0" )


    def test_sequence_not_through_db_2(self):
        from models import PaymentMethod, Transaction, User
        import time

        user, _ = User.objects.get_or_create(username="unit_test_user")
        PaymentMethod.objects.create(payment_method_token = _new_payment_method_token(), user = user)

        ### authorize capture credit

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        Transaction.objects.all().delete()
        pm = PaymentMethod.objects.all()[0]
        t = Transaction(payment_method = pm, processor_token = test_credentials.processor_token)
        t.authorize(20, "USD", billing_reference, customer_reference)
        self.assertTrue( t.errors == [] )
        self.assertTrue( t.amount == "20.0" )
        self.assertTrue( t.transaction_type == "authorize" )
        self.assertTrue( Transaction.objects.all().count() == 1 )
        self.assertTrue( t.fetch() )

        capture_txn = t.capture(18)
        self.assertTrue( capture_txn.errors == [] )
        self.assertTrue( capture_txn.amount == "18.0" )
        self.assertTrue( capture_txn.transaction_type == "capture" )
        self.assertTrue( Transaction.objects.all().count() == 2 )

        credit_txn = capture_txn.credit(10)
        self.assertTrue( credit_txn.errors == [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}] )
        self.assertTrue( credit_txn.amount == "10.0" )
        self.assertTrue( credit_txn.transaction_type == "credit" )
        self.assertTrue( Transaction.objects.all().count() == 3 )


        # check that stuff is in DB

        at_db = Transaction.objects.get(transaction_type = "authorize", transaction_token = t.transaction_token)
        self.assertTrue( at_db.amount == "20.0" )
        self.assertTrue( at_db.fetch() )
        self.assertTrue( at_db.amount == "20.0" )

        cat_db = Transaction.objects.get(transaction_type = "capture", transaction_token = t.transaction_token)
        self.assertTrue( cat_db.amount == "18.0" )
        self.assertTrue( cat_db.fetch() )
        self.assertTrue( cat_db.amount == "18.0" )

        crt_db = Transaction.objects.get(transaction_type = "credit", transaction_token = t.transaction_token)
        self.assertTrue( crt_db.amount == "10.0" )
        self.assertFalse( crt_db.fetch() )
        self.assertTrue( crt_db.amount == "10.0" )
        self.assertTrue( crt_db.errors == [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}])

        self.assertTrue( set([t.transaction_type for t in Transaction.objects.all()]) == set(["credit", "authorize", "capture"]) )



    def test_sequence_through_db_1(self):
        from models import PaymentMethod, Transaction, User
        import time

        user, _ = User.objects.get_or_create(username="unit_test_user")
        PaymentMethod.objects.create(payment_method_token = _new_payment_method_token(), user = user)

        ### purchase void 

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        Transaction.objects.all().delete()
        pm = PaymentMethod.objects.all()[0]
        t = Transaction(payment_method = pm, processor_token = test_credentials.processor_token)
        t.purchase(20, "USD", billing_reference, customer_reference)
        self.assertTrue( t.errors == [] )
        self.assertTrue( t.amount == "20.0" )
        self.assertTrue( t.transaction_type == "purchase" )
        self.assertTrue( Transaction.objects.all().count() == 1 )
        self.assertTrue( t.fetch() )

        t = Transaction.objects.get(reference_id = t.reference_id)

        void_txn = t.void()
        self.assertTrue( void_txn.errors == [] )
        self.assertTrue( void_txn.amount == "20.0" )
        self.assertTrue( void_txn.transaction_type == "void" )
        self.assertTrue( Transaction.objects.all().count() == 2 )
        self.assertTrue( void_txn.fetch() )

        # check that stuff is in DB

        pt_db = Transaction.objects.get(transaction_type = "purchase", transaction_token = t.transaction_token)
        self.assertTrue( pt_db.amount == "20.0" )
        self.assertTrue( pt_db.fetch() )
        self.assertTrue( pt_db.amount == "20.0" )

        vt_db = Transaction.objects.get(transaction_type = "void", transaction_token = t.transaction_token)
        self.assertTrue( vt_db.amount == "20.0" )
        self.assertTrue( vt_db.fetch() )
        self.assertTrue( vt_db.amount == "20.0" )


    def test_sequence_through_db_2(self):
        from models import PaymentMethod, Transaction, User
        import time

        user, _ = User.objects.get_or_create(username="unit_test_user")
        PaymentMethod.objects.create(payment_method_token = _new_payment_method_token(), user = user)

        ### authorize capture credit

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        Transaction.objects.all().delete()
        pm = PaymentMethod.objects.all()[0]
        t = Transaction(payment_method = pm, processor_token = test_credentials.processor_token)
        t.authorize(20, "USD", billing_reference, customer_reference)
        self.assertTrue( t.errors == [] )
        self.assertTrue( t.amount == "20.0", t.amount )
        self.assertTrue( t.transaction_type == "authorize" )
        self.assertTrue( Transaction.objects.all().count() == 1 )
        self.assertTrue( t.fetch() )

        t = Transaction.objects.get(reference_id = t.reference_id)

        capture_txn = t.capture(18)
        self.assertTrue( capture_txn.errors == [] )
        self.assertTrue( capture_txn.amount == "18.0" )
        self.assertTrue( capture_txn.transaction_type == "capture" )
        self.assertTrue( Transaction.objects.all().count() == 2 )

        capture_txn = Transaction.objects.get(reference_id = capture_txn.reference_id)

        credit_txn = capture_txn.credit(10)
        self.assertTrue( credit_txn.errors == [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}], credit_txn.errors)
        self.assertTrue( credit_txn.amount == "10.0" )
        self.assertTrue( credit_txn.transaction_type == "credit" )
        self.assertTrue( Transaction.objects.all().count() == 3 )


        # check that stuff is in DB

        at_db = Transaction.objects.get(transaction_type = "authorize", transaction_token = t.transaction_token)
        self.assertTrue( at_db.amount=="20.0" )
        self.assertTrue( at_db.fetch() )
        self.assertTrue( at_db.amount=="20.0" )

        cat_db = Transaction.objects.get(transaction_type = "capture", transaction_token = t.transaction_token)
        self.assertTrue( cat_db.amount=="18.0" )
        self.assertTrue( cat_db.fetch() )
        self.assertTrue( cat_db.amount=="18.0" )

        crt_db = Transaction.objects.get(transaction_type = "credit", transaction_token = t.transaction_token)
        self.assertTrue( crt_db.amount=="10.0" )
        self.assertFalse( crt_db.fetch() )
        self.assertTrue( crt_db.amount=="10.0" )
        self.assertTrue( crt_db.errors == [{'source': 'processor', 'context': u'processor.transaction', 'key': u'credit_criteria_invalid'}])

        self.assertTrue( set([t.transaction_type for t in Transaction.objects.all()]) == set(["credit", "authorize", "capture"]) )

    def test_migration(self):
        from models import PaymentMethod, Transaction, User
        import time

        user, _ = User.objects.get_or_create(username="unit_test_user")
        PaymentMethod.objects.create(payment_method_token = _new_payment_method_token(), user = user)

        ### authorize capture credit

        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        Transaction.objects.all().delete()
        pm = PaymentMethod.objects.all()[0]
        t = Transaction(payment_method = pm, processor_token = test_credentials.processor_token)
        t.authorize(20, "USD", billing_reference, customer_reference)
        t.amount = ""
        t.currency_code = ""
        t.created_at = None
        t.processor_success = None
        t.save() # t is now a transaction as we had it before adding these fields to the Transaction model.

        t2 = Transaction.objects.get(reference_id = t.reference_id)

        self.assertTrue( t2.amount == "" )
        self.assertTrue( t2.currency_code == "" )
        self.assertTrue( t2.created_at == None )
        self.assertTrue( t2.processor_success == None )

        t2.fetch()

        self.assertTrue( t2.amount == "20.0" )
        self.assertTrue( t2.currency_code == "USD" )
        self.assertTrue( type(t2.created_at) == datetime )
        self.assertTrue( t2.processor_success == True )

        t2.save()
        t3 = Transaction.objects.get(reference_id = t.reference_id)

        self.assertTrue( t3.amount == "20.0" )
        self.assertTrue( t3.currency_code == "USD" )
        self.assertTrue( type(t3.created_at) == datetime )
        self.assertTrue( t3.processor_success == True )



if __name__ == '__main__':
    unittest.main()
