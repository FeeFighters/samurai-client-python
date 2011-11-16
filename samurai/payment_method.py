"""
    Payment method.
    ~~~~~~~~~~~~~~~

    Encapsulation for the stored payment data, and payment methods.
"""
from api_base import ApiBase
from request import Request, fetch_url

class PaymentMethod(ApiBase):
    """
    Proxy for samurai api payment method endpoints.
    Implements `find`, `retain`, `redact` and other related operations.
    """
    top_xml_key = 'payment_method'

    find_url  = 'https://api.samurai.feefighters.com/v1/payment_methods/%s.xml'
    retain_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/retain.xml'
    redact_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/redact.xml'

    def __init__(self, xml_res):
        self.update_fields(xml_res)

    @classmethod
    def find(cls, payment_method_token):
        """
        Gets the payment method details.
        Returns xml data returned from the endpoint converted to python dictionary.
        """
        req = Request(cls.find_url % payment_method_token)
        return cls(fetch_url(req))

    def retain(self):
        """
        Issues `retain` call to samurai API.
        """
        req = Request(self.retain_url % self.payment_method_token, method='post')
        res = fetch_url(req)
        self.update_fields(res)

    def redact(self):
        """
        Issues `redact` call to samurai API.
        """
        req = Request(self.redact_url % self.payment_method_token, method='post')
        res = fetch_url(req)
        self.update_fields(res)
