import test_credentials
from core import *
from core import _xml_to_dict, _dict_to_xml, _request
import time

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

def _new_payment_method_token():
    # set up the payment method for a bunch of tests here
    _, payment_method_token = _transparent_redirect( initial_test_data )
    return payment_method_token

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
    "credit_card[card_number]":"4222222222222",
    "credit_card[cvv]":"000",
    "credit_card[expiry_month]":"1",
    "credit_card[expiry_year]":"2012",
}
   

import unittest

class TestTransparentRedirect():#unittest.TestCase):

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


class TestXMLTODict():#unittest.TestCase):

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
                <message subclass="error" context="gateway.avs" key="country_not_supported" />
                <message subclass="error" context="input.cvv" key="too_short" />
                <message subclass="info" context="gateway.transaction" key="success" />
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
                    <message subclass="error" context="gateway.avs" key="country_not_supported" />
                    <message subclass="error" context="input.cvv" key="too_short" />
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
                <message subclass="error" context="gateway.avs" key="country_not_supported" />
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
                {'context':'gateway.avs', 'key':'country_not_supported', 'source': "samurai"},
            ],
           'info': []
        }}
       
        self.assertEqual(out_dict, expected )
    

class TestDictToXML():#unittest.TestCase):
    def test_dict_to_xml(self):
        payload = {'doc':
            {'last_name': "Fakerson", 'expiry_year': 2012}
        }

        xml = _dict_to_xml(payload)
        xml = parseStringToXML(xml)

        self.assertTrue(xml.documentElement.tagName == "doc")
        self.assertTrue(xml.documentElement.getElementsByTagName('last_name')[0].childNodes[0].nodeValue == "Fakerson")
        self.assertTrue(xml.documentElement.getElementsByTagName('expiry_year')[0].childNodes[0].nodeValue == "2012")

class TestBasicRequest():#unittest.TestCase):

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
    gateway_token = test_credentials.gateway_token)

class TestPaymentMethodMethods():#unittest.TestCase):
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
                gateway_token = test_credentials.gateway_token, payment_method_token = payment_method_token, do_fetch = False)
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
        expected_none = ["created_at", "updated_at", "custom", "is_retained", "is_redacted", "is_sensitive_data_valid", "last_four_digits", "card_type", "first_name", "last_name", "expiry_month", "expiry_year", "address_1", "address_2", "city", "state",  "zip", "country"]

        expected_after = {
            "payment_method_token": payment_method_token,
            "custom": {'a':'b', 'c':{'d':'e'}},
            "is_retained": False,
            "is_redacted": False, 
            "is_sensitive_data_valid":True,
            "errors":[], 
            "info":[], #{'context':'gateway.transaction', 'key':'success', 'source':'samurai'}], 
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
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'response_404'}])

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
            "info":[], #{'context':'gateway.transaction', 'key':'success', 'source':'samurai'}], 
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
            "info":[], #{'context':'gateway.transaction', 'key':'success', 'source':'samurai'}], 
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
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'response_404'}])


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
        self.assertEquals(payment_method.errors, [{'source':'client', 'context':'client', 'key': 'response_404'}])

class TestTransactionMethods(unittest.TestCase):

    def d_test_make_transaction_with_payment_method(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        try:
            transaction = Transaction(feefighters = feefighters, payment_method = payment_method, gateway_token = test_credentials.gateway_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(type(transaction.payment_method), PaymentMethod)
        self.assertEqual(transaction.payment_method.payment_method_token, payment_method_token)
        self.assertEqual(transaction.payment_method.first_name, "Nobody")

        try:
            Transaction(feefighters = feefighters, gateway_token = test_credentials.gateway_token, do_fetch = False)
        except ValueError:
            pass
        except:
            self.fail()
        else:
            self.fail()


    def d_test_make_transaction_credentials(self):
        # with FeeFighters object

        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)

        try:
            transaction = Transaction(feefighters = feefighters, payment_method = payment_method, gateway_token = test_credentials.gateway_token, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(transaction._merchant_key, test_credentials.merchant_key)
        self.assertEqual(transaction._merchant_password, test_credentials.merchant_password)
        self.assertEqual(transaction.gateway_token, test_credentials.gateway_token)

        # same thing, more verbose
        try:
            transaction = Transaction(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                gateway_token = test_credentials.gateway_token, payment_method = payment_method, do_fetch = False)
        except:
            self.fail()

        self.assertEqual(transaction._merchant_key, test_credentials.merchant_key)
        self.assertEqual(transaction._merchant_password, test_credentials.merchant_password)
        self.assertEqual(transaction.gateway_token, test_credentials.gateway_token)

    def d_test_purchase(self):
        payment_method_token = _new_payment_method_token()

        expected_none = ["reference_id", "transaction_token", "created_at", "descriptor", "custom", "transaction_type", "amount", "currency_code", "gateway_success" ]

        expected_after = {
            "custom": {'a':'b'},
            "descriptor": {'c':'d'},
            "transaction_type":"purchase",
            "amount":"20.5",
            "currency_code":"USD",
#            "gateway_token":test_credentials.gateway_token, # why would we even get this back? I'd rather not update it, it shouldn't change.
            "gateway_success": True,
            "errors":[],
        }

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, gateway_token = test_credentials.gateway_token, do_fetch= False)

        for attr_name in expected_none:
            self.assertEqual(getattr(transaction, attr_name), None, attr_name + " not None")

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

        self.assertTrue({'source':'gateway', 'context':'gateway.transaction', 'key':'success'} in transaction.info)

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

    def d_test_bad_purchase(self):
        payment_method_token = _new_payment_method_token()
        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, gateway_token = test_credentials.gateway_token, do_fetch= False)

        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}
        transaction.payment_method.payment_method_token = "bad_token" # just to throw a wrench in the works

        self.assertEqual(transaction.purchase(20.5, "USD", "12345", "321"), False)

        self.assertTrue(bool(transaction.errors))
        
    def test_do_fetch(self):
        payment_method_token = _new_payment_method_token()

        payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token, do_fetch = False)
        transaction = Transaction(feefighters = feefighters, payment_method = payment_method, gateway_token = test_credentials.gateway_token, do_fetch= False)

        transaction.custom = {'a':'b'}
        transaction.descriptor = {'c':'d'}

        # Need unique values to prevent duplicate transaction errors
        billing_reference = "b" + str(int(time.time()))
        customer_reference = "c" + str(int(time.time()))

        self.assertTrue(transaction.purchase(20.5, "USD", billing_reference, customer_reference), transaction.errors)

        transaction_test = Transaction(feefighters = feefighters, reference_id = transaction.reference_id, do_fetch= False)

        for field_name in set(Transaction.field_names) - set(['info', 'errors', 'reference_id']):
            self.assertEqual(getattr(transaction_test, field_name), None, field_name + " not None")

        self.assertEqual(getattr(transaction_test, field_name), None, field_name + " not None")

        self.assertTrue(transaction_test.fetch(), transaction_test.errors)
        self.assertEquals(transaction.errors, [])

        for field_name in set(Transaction.field_names) - set(['errors', 'info']):
            self.assertEqual(getattr(transaction_test, field_name), getattr(transaction, field_name), field_name + " not equal on new transaction: " + str(getattr(transaction_test, field_name)) + "-" + str(getattr(transaction, field_name)))

    def test_make_transaction_with_token(self):
        pass # fail if both are passed



unittest.main()
