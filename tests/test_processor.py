import unittest
import test_helper
from samurai.processor import Processor

class TestPaymentMethod(unittest.TestCase):
    def setUp(self):
        self.pm = test_helper.default_payment_method

    def test_purchase_failure(self):
        token = self.pm.payment_method_token
        trans = Processor.purchase(token, 10)
        errors = ["Couldn't find Processor with token = %s" % token]
        assert trans.errors == errors

    def test_authorize_failure(self):
        token = self.pm.payment_method_token
        trans = Processor.authorize(token, 10)
        errors = ["Couldn't find Processor with token = %s" % token]
        assert trans.errors == errors

if __name__ == '__main__':
    unittest.main()
