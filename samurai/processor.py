"""
    Payment processor for simple purchases.
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Handles purchases.

    Simple purchases are done in a single step and there isn't an option to authorize
    or rollback it.

    Complex purchases are authorized first, and then can be rolled back or completed.
"""
from xmlutils import dict_to_xml
from request import Request, fetch_url
from api_base import ApiBase
from transaction import Transaction

class Processor(ApiBase):
    """
    `Processor` deals with payments.
    """
    purchase_url = 'https://api.samurai.feefighters.com/v1/processors/%s/purchase.xml'
    authorize_url = 'https://api.samurai.feefighters.com/v1/processors/%s/authorize.xml'

    purchase_optional_data = set(('billing_reference', 'customer_reference',
                                 'descriptor', 'custom'))

    @classmethod
    def purchase(cls, payment_method_token, amount, **options):
        """
        Makes a simple purchase call.
        Returns a transaction object.
        """
        return cls.transact(payment_method_token, amount,
                            'purchase', cls.purchase_url, options)

    @classmethod
    def authorize(cls, payment_method_token, amount, **options):
        """
        `authorize` doesn't charge credit card. It only reserves the transaction amount.
        It returns a `Transaction` object which can be `captured` or `reversed`.
        """
        return cls.transact(payment_method_token, amount,
                            'authorize', cls.authorize_url, options)

    @classmethod
    def transact(cls, payment_method_token, amount, transaction_type,
                 endpoint, options):
        """
        Meant to be used internally and shouldn't be called from outside.

        Makes an `authorize` or `purchase` request.

        `authorize` and `purchase` have same flow, except for `transaction_type` and
        `endpoint`.
        """
        purchase_data = cls.construct_options(payment_method_token, transaction_type,
                                              amount, options)
        # Send payload and return transaction.
        req = Request(endpoint % payment_method_token, purchase_data, method='post')
        req.add_header("Content-Type", "application/xml")
        return Transaction(fetch_url(req))

    @classmethod
    def construct_options(cls, payment_method_token, transaction_type,
                          amount, options):
        """
        Constructs XML payload to be sent for the transaction.
        """
        # Pick relevant options and construct xml payload.
        purchase_data = {
            'transaction': {
                'type': transaction_type,
                'currency_code': 'USD',
                'amount': amount
            }
        }
        options = dict((k, v) for k, v in options.iteritems()
                       if k in cls.purchase_optional_data)
        options['payment_method_token'] = payment_method_token
        purchase_data['transaction'].update(options)
        purchase_data = dict_to_xml(purchase_data)
        return purchase_data
