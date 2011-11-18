"""
    Payment method.
    ~~~~~~~~~~~~~~~

    Encapsulation for the stored payment data, and payment methods.
"""
from api_base import ApiBase
from request import Request, fetch_url
from xmlutils import dict_to_xml

class PaymentMethod(ApiBase):
    """
    Proxy for samurai api payment method endpoints.
    Implements `find`, `retain`, `redact` and other related operations.
    """
    top_xml_key = 'payment_method'

    find_url  = 'https://api.samurai.feefighters.com/v1/payment_methods/%s.xml'
    retain_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/retain.xml'
    redact_url = 'https://api.samurai.feefighters.com/v1/payment_methods/%s/redact.xml'
    create_url = 'https://api.samurai.feefighters.com/v1/payment_methods.xml'
    update_url  = 'https://api.samurai.feefighters.com/v1/payment_methods/%s.xml'

    create_data = set(('card_number', 'cvv', 'expiry_month', 'expiry_year',
                       'first_name', 'last_name', 'address_1', 'address_2',
                       'city', 'state', 'zip', 'custom', 'sandbox'))

    def __init__(self, xml_res):
        super(PaymentMethod, self).__init__()
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
        return self

    def redact(self):
        """
        Issues `redact` call to samurai API.
        """
        req = Request(self.redact_url % self.payment_method_token, method='post')
        res = fetch_url(req)
        self.update_fields(res)
        return self

    @classmethod
    def create(cls, card_number, cvv, expiry_month, expiry_year, **other_args):
        """
        Creates a payment method.

        Transaprent redirects are favored method for creating payment methods.
        Using this call places the burden of PCI compliance on the client since the
        data passes through it.
        """
        payload = {
            'payment_method': {
                'card_number': card_number,
                'cvv': cvv,
                'expiry_month': expiry_month,
                'expiry_year': expiry_year,
            }
        }
        optional_data = dict((k, v) for k, v in other_args.iteritems()
                             if k in cls.create_data)
        payload['payment_method'].update(**optional_data)
        payload = dict_to_xml(payload)

        # Send payload and return payment method.
        req = Request(cls.create_url, payload, method='post')
        req.add_header("Content-Type", "application/xml")
        return cls(fetch_url(req))

    def update(self, **other_args):
        """
        Updates a payment method.

        Payment method can't be updated once it has been retained or redacted.
        """
        payload = {
            'payment_method': {
            }
        }
        optional_data = dict((k, v) for k, v in other_args.iteritems()
                             if k in self.create_data)
        payload['payment_method'].update(**optional_data)
        payload = dict_to_xml(payload)

        # Send payload and return payment method.
        req = Request(self.update_url % self.payment_method_token, payload, method='put')
        req.add_header("Content-Type", "application/xml")
        return type(self)(fetch_url(req))
