from django.conf import settings
import feefighter.core
import hashlib
from core import PaymentMethod as CorePaymentMethod

def unique_id_for_user(user):
    return hashlib.sha256(str(user.id) + settings.FEEFIGHTERSALT) # perhaps?

class PaymentMethod(Model, PaymentMethod):
    payment_method_token = CharField(unique = True)
    user = ForeignKey(User)

    def __init__(self, *args, **kwargs):
        super(PaymentMethod, self).__init__(*args, **kwargs)

        self._core_payment_method = CorePaymentMethod(feefighters = settings.FEEFIGHTERS_CREDENTIALS,
            payment_method_token, do_fetch = kwargs.get('do_fetch', True))

#    def clean(self):
#        """
#        checks the custom field for a unique identifier related to self.user as a security measure
#        """
#        self.custom['django_user_unique'] ...
#        self.custom['django_prev_payment_method_token'] ...
#        ...
       

#class TransactionModel(Model, Transaction):
#    transaction_method_token_field = CharField(unique = True)
#    payment_method = ForeignKey(PaymentMethod)
