"""
    Transaction
    ~~~~~~~~~~~~

    Transactions encapsulate the returned data from the api when a transaction is made
    agains a payment token.
"""
from xmlutils import dict_to_xml
from api_base import ApiBase
from request import Request, fetch_url
from errors import UnauthorizedTransactionError

class Transaction(ApiBase):
    """
    A completed or authorized transaction.
    This class can be used to introspect trasnaction data, as well as perform transaction
    operations viz. reverse, authorize, capture etc.

    In case of simple purchases, the returned data will be mostly used for inspection.

    In complex transactions, opertaions on it are used to perform or cancel it.
    """
    top_xml_key = 'transaction'

    find_url = 'https://api.samurai.feefighters.com/v1/transactions/%s.xml'
    capture_url = 'https://api.samurai.feefighters.com/v1/transactions/%s/capture.xml'
    reverse_url = 'https://api.samurai.feefighters.com/v1/transactions/%s/reverse.xml'
    credit_url = 'https://api.samurai.feefighters.com/v1/transactions/%s/credit.xml'
    void_url = 'https://api.samurai.feefighters.com/v1/transactions/%s/void.xml'

    def __init__(self, xml_res):
        """
        Initializes transaction data by parsing `xml_res`.
        """
        super(Transaction, self).__init__()
        self.update_fields(xml_res)

    @classmethod
    def find(cls, reference_id):
        """
        Gets the transaction details.
        Returns xml data returned from the endpoint converted to python dictionary.
        """
        req = Request(cls.find_url % reference_id)
        return cls(fetch_url(req))

    def message_block(self, parsed_res):
        """
        Returns the message block from the `parsed_res`
        """
        return (parsed_res.get(self.top_xml_key) and
                parsed_res[self.top_xml_key].get('processor_response') and
                parsed_res[self.top_xml_key]['processor_response'].get('messages'))

    def check_for_errors(self, parsed_res):
        """
        Checks `parsed_res` for error blocks.
        If the transaction failed, sets `self.errors`
        Else delegates to superclass.
        """
        if parsed_res.get(self.top_xml_key):
            if not parsed_res[self.top_xml_key]['processor_response']['success']:
                message_block = self.message_block(parsed_res)
                if message_block and message_block.get('message'):
                    message = message_block['message']
                    self.errors = message if isinstance(message, list) else [message]
                return True
        return super(Transaction, self).check_for_errors(parsed_res)

    def capture(self, amount):
        """
        Captures transaction. Works only if the transaction is authorized.

        Returns a new transaction.
        """
        return self.transact(self.capture_url, amount)

    def credit(self, amount):
        """
        Credits transaction. Works only if the transaction is authorized.
        Depending on the settlement status of the transaction, and the behavior of the
        processor endpoint, this API call may result in a `void`, `credit`, or `refund`.

        Returns a new transaction.
        """
        return self.transact(self.credit_url, amount)

    def reverse(self, amount):
        """
        Reverses transaction. Works only if the transaction is authorized.

        Returns a new transaction.
        """
        return self.transact(self.reverse_url, amount)

    def void(self):
        """
        Voids transaction. Works only if the transaction is authorized.

        Returns a new transaction.
        """
        return self.transact(self.void_url)

    def transact(self, endpoint, amount=None):
        """
        Meant to be used internally and shouldn't be called from outside.

        Makes the specified call and returns resultant `transaction`.
        """
        if not getattr(self, 'transaction_token', None):
            raise UnauthorizedTransactionError('Transaction is not authorized.')
        if amount:
            data = dict_to_xml({'amount': amount})
            req = Request(endpoint % self.transaction_token, data, method='post')
        else:
            req = Request(endpoint % self.transaction_token, method='post')
        res = fetch_url(req)
        return type(self)(res)
