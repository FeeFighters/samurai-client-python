"""
Payment method.
~~~~~~~~~~~~~~~

Encapsulation for the stored payment data, and payment methods.
"""
from xmlutils import xml_to_dict
from request import Request, fetch_url

class PaymentMethod(object):
    """
    Proxy for samurai api payment method endpoints.
    Implements `find`, `retain`, `redact` and other related operations.
    """
    find_url  = 'https://api.samurai.feefighters.com/v1/payment_methods/%s.xml'
    retain_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/retain.xml'
    redact_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/redact.xml'

    def __init__(self, payment_token, xml_res):
        self.xml_data = xml_res
        self.payment_token = payment_token
        self.dict_data = xml_to_dict(xml_res)

    @classmethod
    def find(cls, payment_token):
        """
        Gets the payment method details.
        Returns xml data returned from the endpoint converted to python dictionary.
        """
        req = Request(cls.find_url % payment_token)
        return cls(payment_token, fetch_url(req))

    def is_sensitive_data_valid(self):
        """
        Predicate for checking data validity.
        """
        return self.dict_data['is_sensitive_data_valid']

    def retain(self):
        """
        Issues `retain` call to samurai API.
        """
        req = Request(self.retain_url % self.payment_token, method='post')
        res = fetch_url(req)
        return xml_to_dict(res), res

    def redact(self):
        """
        Issues `redact` call to samurai API.
        """
        req = Request(self.redact_url % self.payment_token, method='post')
        res = fetch_url(req)
        return xml_to_dict(res), res
