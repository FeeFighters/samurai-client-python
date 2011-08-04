import json
from django.conf import settings 
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from models import secret_id_for_user
from edulender.samurai_client_python.models import PaymentMethod


def payment_method_redirect(request, update):
    if update:
        success_redirect = settings.SAMURAI_UPDATEMETHOD_REDIRECT
        error_redirect = settings.SAMURAI_UPDATEMETHOD_REDIRECT
    else:
        success_redirect = settings.SAMURAI_NEWMETHOD_REDIRECT
        error_redirect = settings.SAMURAI_NEWMETHOD_REDIRECT

    if not 'payment_method_token' in request.GET:
        return HttpResponseRedirect( reverse(error_redirect ) )
 
    new_payment_method = PaymentMethod(payment_method_token = request.GET['payment_method_token'], user = request.user)

    if not new_payment_method.fetch() or not new_payment_method.is_sensitive_data_valid:
        return HttpResponseRedirect( reverse(error_redirect ) 
            + "?payment_method_token=" + new_payment_method.payment_method_token )

    try:
        new_payment_method.full_clean()

        if update:
            old_payment_method = PaymentMethod.objects.get(payment_method_token = new_payment_method.custom['django_prev_payment_method_token'])
            if old_payment_method.redact():
                old_payment_method.delete()

        new_payment_method.save()

        return HttpResponseRedirect( reverse(success_redirect ) 
            + "?payment_method_token=" + new_payment_method.payment_method_token )
    except ValidationError: # not attached to the right user
        return HttpResponseRedirect( reverse(error_redirect )
            + "?payment_method_token=" + new_payment_method.payment_method_token )


@login_required
def new_payment_method_redirect(request):
    return payment_method_redirect(request, False)


@login_required
def update_payment_method_redirect(request):
    return payment_method_redirect(request, True)


def get_transparent_redirect_form_initial(user, base_url, payment_method = None, update = False): 
    init = {}

    if payment_method != None:
        init.update(payment_method.as_dict()) # important to note that this may carry over custom set by the client consumer
        init["custom"] = dict(init["custom"]) # make a copy so I don't change the data in the payment_method
        if update:
            init["custom"]["django_prev_payment_method_token"] = payment_method.payment_method_token # passing on to the next payment method
    else:
        init["custom"] = {}
    
    init['custom']['django_user_unique'] = secret_id_for_user(user)

    init['merchant_key'] = settings.SAMURAI_CREDENTIALS.merchant_key

    if update:
        init['redirect_url'] = base_url + reverse('samurai-update-payment-method-redirect')
    else:
        init['redirect_url'] = base_url + reverse('samurai-new-payment-method-redirect')

    init['custom'] = json.dumps(init['custom'])
    return init
