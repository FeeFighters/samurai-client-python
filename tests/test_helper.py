import sys
sys.path.append('..')

import samurai.config as config
from samurai.payment_method import PaymentMethod

config.merchant_key = 'a1ebafb6da5238fb8a3ac9f6'
config.merchant_password = 'ae1aa640f6b735c4730fbb56'

default_payment_method = PaymentMethod.create('4242424242424242',
                                              '133', '07', '12', first_name='first_name',
                                              last_name='last_name', sandbox=True)
