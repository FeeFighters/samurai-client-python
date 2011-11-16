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
