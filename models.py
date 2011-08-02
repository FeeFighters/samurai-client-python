from django.db import models
from django.conf import settings
import hashlib
from django.contrib.auth.models import User
from core import PaymentMethod as CorePaymentMethod

def unique_id_for_user(user):
    return hashlib.sha256(str(user.id) + settings.FEEFIGHTERSALT) # perhaps?

class PaymentMethod(models.Model):
    payment_method_token = models.CharField(max_length=100, editable=False)
    user = models.ForeignKey(User)

    def __init__(self, *args, **kwargs):
        super(PaymentMethod, self).__init__(*args, **kwargs)

        self._core_payment_method = CorePaymentMethod(feefighters = settings.FEEFIGHTERS_CREDENTIALS,
            payment_method_token = kwargs["payment_method_token"], do_fetch = kwargs.get('do_fetch', True))

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
