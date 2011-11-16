"""
    Transaction
    ~~~~~~~~~~~~

    Transactions encapsulate the returned data from the api when a transaction is made
    agains a payment token.
"""
from api_base import ApiBase
from request import Request, fetch_url

class Transaction(ApiBase):
    """
    A completed or authorized transaction.
    This class can be used to introspect trasnaction data, as well as perform transaction
    operations viz. reverse, authorize, capture etc.

    In case of simple purchases, the returned data will be mostly used for inspection.

    In complex transactions, opertaions on it are used to perform or cancel it.
    """
    top_xml_key = 'transaction'

    def __init__(self, xml_res):
        """
        Initializes transaction data by parsing `xml_res`.
        """
        super(ApiBase, self).__init__()
        self.update_fields(xml_res)

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
        if not parsed_res[self.top_xml_key]['processor_response']['success']:
            message_block = self.message_block(parsed_res)
            if message_block and message_block.get('message'):
                self.errors = message_block['message']
            return True
        return super(ApiBase, self).check_for_errors(parsed_res)
