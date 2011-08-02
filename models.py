from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import hashlib
from django.contrib.auth.models import User
from core import PaymentMethod as CorePaymentMethod

def secret_id_for_user(user):
    hash = hashlib.sha1()
    hash.update(str(user.id) + settings.FEEFIGHTERS_SALT)
    return hash.hexdigest()

class PaymentMethod(models.Model):
    payment_method_token = models.CharField(max_length=100, editable=False, unique=True)
    user = models.ForeignKey(User)

    def __init__(self, *args, **kwargs):
        super(PaymentMethod, self).__init__(*args, **kwargs)

        # Gonna do_fetch = False here. We don't want to fetch every object every time we run PaymentMethod.objects.all() in the shell
        # And we won't have control over fetching when we do a filter.
        self._core_payment_method = CorePaymentMethod(feefighters = settings.FEEFIGHTERS_CREDENTIALS,
            payment_method_token = self.payment_method_token, do_fetch = False)

        self._get_fields_from_core()

    def fetch(self):
        self._core_payment_method.fetch()
        self._get_fields_from_core()

    def redact(self):
        self._core_payment_method.redact()
        self._get_fields_from_core()

    def retain(self):
        self._core_payment_method.retain()
        self._get_fields_from_core()

    def update(self):
        self._set_fields_into_core()
        self._core_payment_method.update()
        self._get_fields_from_core()

    def _get_fields_from_core(self):
        for field_name in self._core_payment_method.field_names + ['payment_method_token', 'populated']:
            setattr(self, field_name, getattr(self._core_payment_method, field_name))

    def _set_fields_into_core(self):
        for field_name in self._core_payment_method.field_names:
            setattr(self._core_payment_method, field_name, getattr(self, field_name))

    def clean(self):
        "checks the custom field for a unique identifier related to self.user as a security measure"

        if self.custom.get('django_user_unique', None) != secret_id_for_user(self.user):
            raise ValidationError("Secret user id doesn't match!")
        if 'django_prev_payment_method_token' in self.custom:
            prev_payment_method_token_query = PaymentMethod.objects.filter(self.custom['django_prev_payment_method_token'])
            if not prev_payment_method_token_query.exists():
                raise ValidationError("Old payment method token not in database.")
            if prev_payment_method_token_query[0].user != self.user:
                raise ValidationError("Old payment method token not in database.")
       
#    def replace(self, payment_method):
#
#       self.payment_method_token = 
#       self.delete()

#class TransactionModel(Model, Transaction):
#    transaction_method_token_field = CharField(unique = True)
#    payment_method = ForeignKey(PaymentMethod)
