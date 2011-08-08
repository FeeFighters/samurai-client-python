from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import hashlib
from django.contrib.auth.models import User
from core import PaymentMethod as CorePaymentMethod, Transaction as CoreTransaction

def secret_id_for_user(user):
    hash = hashlib.sha1()
    hash.update(str(user.id) + settings.SAMURAI_SALT)
    return hash.hexdigest()

class RemoteObject(object):
    def as_dict(self):
        return self._core_remote_object.as_dict()

class PaymentMethod(models.Model, RemoteObject):
    payment_method_token = models.CharField(max_length=100, editable=False, unique=True)
    user = models.ForeignKey(User, editable=False)

    def __init__(self, *args, **kwargs):
        super(PaymentMethod, self).__init__(*args, **kwargs)

        # Gonna do_fetch = False here. We don't want to fetch every object every time we run PaymentMethod.objects.all() in the shell
        # And we won't have control over fetching when we do a filter.
        self._core_remote_object = CorePaymentMethod(feefighters = settings.SAMURAI_CREDENTIALS,
            payment_method_token = self.payment_method_token, do_fetch = False)

        self._get_fields_from_core()

    def _get_fields_from_core(self):
        for field_name in self._core_remote_object.field_names + ['payment_method_token', 'populated']:
            setattr(self, field_name, getattr(self._core_remote_object, field_name))

    def _set_fields_into_core(self):
        for field_name in self._core_remote_object.field_names:
            setattr(self._core_remote_object, field_name, getattr(self, field_name))

    def fetch(self):
        self._set_fields_into_core()
        result = self._core_remote_object.fetch()
        self._get_fields_from_core()
        return result

    def redact(self):
        self._set_fields_into_core()
        result = self._core_remote_object.redact()
        self._get_fields_from_core()
        return result

    def retain(self):
        self._set_fields_into_core()
        result = self._core_remote_object.retain()
        self._get_fields_from_core()
        return result

    def update(self):
        self._set_fields_into_core()
        result = self._core_remote_object.update()
        self._get_fields_from_core()
        return result


    def clean(self):
        "checks the custom field for a unique identifier related to self.user as a security measure"

        if self.custom.get('django_user_unique', None) != secret_id_for_user(self.user):
            raise ValidationError("Secret user id doesn't match!")
        if 'django_prev_payment_method_token' in self.custom:
            prev_payment_method_token_query = PaymentMethod.objects.filter(payment_method_token = self.custom['django_prev_payment_method_token'])
            if not prev_payment_method_token_query.exists():
                raise ValidationError("Old payment method token not in database.")
            if prev_payment_method_token_query[0].user != self.user:
                raise ValidationError("Old payment method token not in database.")
       
#    def replace(self, payment_method):
#
#       self.payment_method_token = 
#       self.delete()

class Transaction(models.Model, RemoteObject):
    transaction_token = models.CharField(max_length=100, editable=False)
    processor_token = models.CharField(max_length=100, editable=False)
    reference_id = models.CharField(unique = True, max_length=100, editable=False)
    payment_method = models.ForeignKey(PaymentMethod, editable=False)
    transaction_type = models.CharField(max_length=20, editable=False)

    def __init__(self, *args, **kwargs):
        super(Transaction, self).__init__(*args, **kwargs)

        # Gonna do_fetch = False here. We don't want to fetch every object every time we run Transaction.objects.all() in the shell
        # And we won't have control over fetching when we do a filter.
        if self.reference_id == None:
            self._core_remote_object = CoreTransaction(feefighters = settings.SAMURAI_CREDENTIALS,
                payment_method = self.payment_method._core_remote_object, processor_token = self.processor_token, do_fetch = False)
        else:
            self._core_remote_object = CoreTransaction(feefighters = settings.SAMURAI_CREDENTIALS,
                reference_id = self.reference_id, processor_token = self.processor_token, do_fetch = False)

        # exclude here since overwriting before fetch could wipe out what's from the DB
        self._get_fields_from_core(exclude = ["transaction_token", "reference_id", "transaction_type"])
        self._set_fields_into_core()

    def _get_fields_from_core(self, exclude = []):
        for field_name in set(self._core_remote_object.field_names + ['populated']) - set(['payment_method', 'processor_token']) - set(exclude):
            setattr(self, field_name, getattr(self._core_remote_object, field_name))

        # self.payment_method should really always be set, but I'm avoiding unnecessary errors if I made a mistake somewhere
        if self.payment_method and self._core_remote_object.payment_method: 
            self.payment_method._core_remote_object = self._core_remote_object.payment_method

    def _set_fields_into_core(self):
        for field_name in set(self._core_remote_object.field_names) - set(['payment_method', 'processor_token']):
            setattr(self._core_remote_object, field_name, getattr(self, field_name))
        self._core_remote_object.payment_method = self.payment_method._core_remote_object
        

    def _save_new_transaction(self, new_transaction_core):
        new_transaction = Transaction(transaction_token = new_transaction_core.transaction_token, reference_id = new_transaction_core.reference_id,
            payment_method = self.payment_method, transaction_type = new_transaction_core.transaction_type) 
        try:
            new_transaction.full_clean()
        except:
            return None
        else:
            return new_transaction

    def purchase(self, amount, currency_code, billing_reference, customer_reference):
        self._set_fields_into_core()
        if self._core_remote_object.purchase(amount, currency_code, billing_reference, customer_reference):
            self._get_fields_from_core()
            try:
                self.full_clean()
            except:
                return False
            self.save()
            return True
        else:
            return False

    def authorize(self, amount, currency_code, billing_reference, customer_reference):
        self._set_fields_into_core()
        if self._core_remote_object.authorize(amount, currency_code, billing_reference, customer_reference):
            self._get_fields_from_core()
            try:
                self.full_clean()
            except:
                return False
            self.save()
            return True
        else:
            return False

    def capture(self, amount):
        self._set_fields_into_core()
        new_transaction_core = self._core_remote_object.capture(amount)
        return self._save_new_transaction(new_transaction_core)

    def void(self):
        self._set_fields_into_core()
        new_transaction_core = self._core_remote_object.void()
        return self._save_new_transaction(new_transaction_core)

    def credit(self, amount):
        self._set_fields_into_core()
        new_transaction_core = self._core_remote_object.credit(amount)
        return self._save_new_transaction(new_transaction_core)

    def fetch(self):
        self._set_fields_into_core()
        result = self._core_remote_object.fetch()
        self._get_fields_from_core()
        return result
