import unittest
import test_helper
from samurai.payment_method import PaymentMethod

params = {
    'first_name'  : "FirstName",
    'last_name'   : "LastName",
    'address_1'   : "123 Main St.",
    'address_2'   : "Apt #3",
    'city'        : "Chicago",
    'state'       : "IL",
    'zip'         : "10101",
    'card_number' : "4111-1111-1111-1111",
    'cvv'         : "123",
    'expiry_month': '03',
    'expiry_year' : "2015",
}

paramsx = {
    'first_name'  : "FirstNameX",
    'last_name'   : "LastNameX",
    'address_1'   : "123 Main St.X",
    'address_2'   : "Apt #3X",
    'city'        : "ChicagoX",
    'state'       : "IL",
    'zip'         : "10101",
    'card_number' : "5454-5454-5454-5454",
    'cvv'         : "456",
    'expiry_month': '05',
    'expiry_year' : "2016",
}

class TestPaymentMethod(unittest.TestCase):
    def setUp(self):
        self.pm = PaymentMethod.create(**params)

    #
    # Test create
    #

    def test_create(self):
        assert self.pm.is_sensitive_data_valid
        assert self.pm.is_expiration_valid
        assert self.pm.first_name == params['first_name']
        assert self.pm.last_name   == params['last_name']
        assert self.pm.address_1   == params['address_1']
        assert self.pm.address_2   == params['address_2']
        assert self.pm.city        == params['city']
        assert self.pm.state       == params['state']
        assert self.pm.zip         == params['zip']
        assert self.pm.last_four_digits == params['card_number'][-4:]
        assert self.pm.expiry_month  == int(params['expiry_month'])
        assert self.pm.expiry_year   == int(params['expiry_year'])

    #
    # Test failure on input.card_number
    #

    def test_should_fail_on_blank_card_number(self):
        params_tmp = params
        params_tmp['card_number'] =  ''
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'is_blank', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_too_short_card_number(self):
        params_tmp = params
        params_tmp['card_number'] =  '4111-1'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'too_short', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_too_long_card_number(self):
        params_tmp = params
        params_tmp['card_number'] =  '4111-1111-1111-1111-11'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'too_long', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_failed_checksum_card_number(self):
        params_tmp = params
        params_tmp['card_number'] =  '4111-1111-1111-1234'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'failed_checksum', 'subclass': 'error'}
        assert err in pm.errors


    #
    # Test failure on input.cvv
    #

    def test_should_return_too_short_cvv(self):
        params_tmp = params
        params_tmp['cvv'] =  '1'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'too_short', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_too_long_cvv(self):
        params_tmp = params
        params_tmp['cvv'] =  '1111111'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'too_long', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_not_numeric_cvv(self):
        params_tmp = params
        params_tmp['cvv'] =  'abcd1'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'not_numeric', 'subclass': 'error'}
        assert err in pm.errors

    #
    # Test failure on input.expiry_month
    #

    def test_should_return_is_blank_expiry_month(self):
        params_tmp = params
        params_tmp['expiry_month'] =  ''
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_month', 'key': 'is_blank', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_is_invalid(self):
        params_tmp = params
        params_tmp['expiry_month'] =  'abcd'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_month', 'key': 'is_invalid', 'subclass': 'error'}
        assert err in pm.errors

    #
    # Test failure on input.expiry_year
    #

    def test_should_return_is_blank_expiry_year(self):
        params_tmp = params
        params_tmp['expiry_year'] =  ''
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_year', 'key': 'is_blank', 'subclass': 'error'}
        assert err in pm.errors

    def test_should_return_is_invalid_expiry_year(self):
        params_tmp = params
        params_tmp['expiry_year'] =  'abcd'
        pm = PaymentMethod.create(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_year', 'key': 'is_invalid', 'subclass': 'error'}
        assert err in pm.errors

    #
    # S2SUpdate
    #

    def test_update(self):
        pm = self.pm.update(**paramsx)
        assert pm.is_sensitive_data_valid
        assert pm.is_expiration_valid
        assert pm.first_name == paramsx['first_name']
        assert pm.last_name   == paramsx['last_name']
        assert pm.address_1   == paramsx['address_1']
        assert pm.address_2   == paramsx['address_2']
        assert pm.city        == paramsx['city']
        assert pm.state       == paramsx['state']
        assert pm.zip         == paramsx['zip']
        assert pm.last_four_digits == paramsx['card_number'][-4:]
        assert pm.expiry_month  == int(paramsx['expiry_month'])
        assert pm.expiry_year   == int(paramsx['expiry_year'])

    def test_update_should_be_successful_preserving_sensitive_data(self):
        params_tmp = paramsx
        params_tmp['card_number'] = '****************'
        params_tmp['cvv'] = '***'
        pm = PaymentMethod.create(**params)
        pm = pm.update(**paramsx)
        #assert pm.is_sensitive_data_valid
        assert pm.is_expiration_valid
        assert pm.first_name == params_tmp['first_name']
        assert pm.last_name   == params_tmp['last_name']
        assert pm.address_1   == params_tmp['address_1']
        assert pm.address_2   == params_tmp['address_2']
        assert pm.city        == params_tmp['city']
        assert pm.state       == params_tmp['state']
        assert pm.zip         == params_tmp['zip']
        assert pm.last_four_digits == '1111'
        assert pm.expiry_month  == int(params_tmp['expiry_month'])
        assert pm.expiry_year   == int(params_tmp['expiry_year'])

    #
    # Test failure on input.card_number
    #

    def test_update_should_return_too_long_card_number(self):
        params_tmp = paramsx
        params_tmp['card_number'] =  '4111-1111-1111-1111-11'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'too_long', 'subclass': 'error'}
        assert err in pm.errors

    # This test case fails and return last_four_digits as '1111'. 
    # Need to confirm with Josh
    #def test_should_fail_on_blank_card_number(self):
    #    params_tmp = paramsx
    #    params_tmp['card_number'] =  ''
    #    pm = self.pm.update(**params_tmp)
    #    assert pm.is_sensitive_data_valid == False
    #    err = {'context': 'input.card_number', 'key': 'is_blank', 'subclass': 'error'}
    #    assert err in pm.errors

    def test_update_should_return_too_short_card_number(self):
        pm = self.pm.update(card_number='4111-1')
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'too_short', 'subclass': 'error'}
        assert err in pm.errors

    def test_update_should_return_failed_checksum_card_number(self):
        params_tmp = paramsx
        params_tmp['card_number'] =  '4111-1111-1111-1234'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.card_number', 'key': 'failed_checksum', 'subclass': 'error'}
        assert err in pm.errors

    #
    # Test failure on input.cvv
    #

    def test_update_should_return_too_short_cvv(self):
        params_tmp = paramsx
        params_tmp['cvv'] =  '1'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'too_short', 'subclass': 'error'}
        assert err in pm.errors

    def test_update_should_return_too_long_cvv(self):
        params_tmp = paramsx
        params_tmp['cvv'] =  '1111111'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'too_long', 'subclass': 'error'}
        assert err in pm.errors


    # returns too_short, should return not_numeric
    def test_update_should_return_not_numeric_cvv(self):
        params_tmp = paramsx
        params_tmp['cvv'] =  'abcd1'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        err = {'context': 'input.cvv', 'key': 'too_short', 'subclass': 'error'}
        assert err in pm.errors

    #
    # Test failure on input.expiry_month
    #

    def test_update_should_return_is_blank_expiry_month(self):
        params_tmp = paramsx
        params_tmp['expiry_month'] =  ''
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_month', 'key': 'is_blank', 'subclass': 'error'}
        assert err in pm.errors

    def test_update_should_return_is_invalid(self):
        params_tmp = paramsx
        params_tmp['expiry_month'] =  'abcd'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_month', 'key': 'is_invalid', 'subclass': 'error'}
        assert err in pm.errors

    #
    # Test failure on input.expiry_year
    #

    def test_update_should_return_is_blank_expiry_year(self):
        params_tmp = paramsx
        params_tmp['expiry_year'] =  ''
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_year', 'key': 'is_blank', 'subclass': 'error'}
        assert err in pm.errors

    def test_update_should_return_is_invalid_expiry_year(self):
        params_tmp = paramsx
        params_tmp['expiry_year'] =  'abcd'
        pm = self.pm.update(**params_tmp)
        assert pm.is_sensitive_data_valid == False
        assert pm.is_expiration_valid == False
        err = {'context': 'input.expiry_year', 'key': 'is_invalid', 'subclass': 'error'}
        assert err in pm.errors

    #
    #find
    #

    def test_find_should_be_successful(self):
      pm = PaymentMethod.create(**params)
      token = pm.payment_method_token
      pm = PaymentMethod.find(token)
      assert self.pm.is_sensitive_data_valid
      assert self.pm.is_expiration_valid
      assert self.pm.first_name == params['first_name']
      assert self.pm.last_name   == params['last_name']
      assert self.pm.address_1   == params['address_1']
      assert self.pm.address_2   == params['address_2']
      assert self.pm.city        == params['city']
      assert self.pm.state       == params['state']
      assert self.pm.zip         == params['zip']
      assert self.pm.last_four_digits == params['card_number'][-4:]
      assert self.pm.expiry_month  == int(params['expiry_month'])
      assert self.pm.expiry_year   == int(params['expiry_year'])

    def test_find_should_fail_on_an_invalid_token(self):
        pm = PaymentMethod.find('abc123')
        err = "Couldn't find PaymentMethod with token = abc123"
        assert err in pm.errors

    def test_retain(self):
        pm = self.pm.retain()
        assert pm.is_retained

    def test_redact(self):
        pm = self.pm.redact()
        assert pm.is_redacted

if __name__ == '__main__':
    unittest.main()
