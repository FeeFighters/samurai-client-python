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

    purchase_optional_data = set(('billing_reference', 'customer_reference',
                                 'descriptor', 'custom'))

    @classmethod
    def purchase(cls, payment_method_token, amount, **options):
        """
        Makes a simple purchase call.
        Returns a transaction object.
        """
        # Pick relevant options and construct xml payload.
        purchase_data = {
            'transaction': {
                'type': 'purchase',
                'currency_code': 'USD',
                'amount': amount
            }
        }
        options = dict((k, v) for k, v in options.iteritems()
                       if k in cls.purchase_optional_data)
        options['payment_method_token'] = payment_method_token
        purchase_data['transaction'].update(options)
        purchase_data = dict_to_xml(purchase_data)

        # Send payload and return transaction.
        req = Request(cls.purchase_url % payment_method_token, purchase_data, method='post')
        req.add_header("Content-Type", "application/xml")
        return Transaction(fetch_url(req))
