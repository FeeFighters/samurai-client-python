import json
from django.conf import settings 
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from models import secret_id_for_user
from edulender.samurai_client_python.models import PaymentMethod


def payment_method_redirect(request, update ):
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
            old_payment_method.redact()
            old_payment_method.disabled = True
            old_payment_method.save()

        new_payment_method.retain()
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
    update_url = update

    if payment_method != None:
        # important to note that this may carry over custom set by the client consumer, which we shouldn't change
        payment_method_data = payment_method.as_dict() 
        for key, value in payment_method_data.iteritems():
            field = {'value' : value}
            if value == "" and key != "address_2":
                field['error'] = "This field is required"
            init[key] = field
        init["custom"]['value'] = dict(init["custom"]['value']) # make a copy so I don't change the data in the payment_method

        if update:
            init["payment_method_token"] = {'value': payment_method.payment_method_token} # making sure that the blank items (or "*****"'d secret items) in the next generated PM are replaced with the values from this PM
            if PaymentMethod.objects.filter(payment_method_token = payment_method.payment_method_token, user = user).exists():
                init["custom"]['value']["django_prev_payment_method_token"] = payment_method.payment_method_token # passing on to the next payment method
            else:
                old_token_to_update = payment_method.custom.get('django_prev_payment_method_token', "not in DB")
                if PaymentMethod.objects.filter(payment_method_token = old_token_to_update, user = user).exists():
                    # we probably tried to update the payment method, but the replacement had an error, so it wasn't saved
                    # so we're propagating the token to update
                    init["custom"]['value']["django_prev_payment_method_token"] = old_token_to_update 
                else:
                    update_url = False
    else:
        init["custom"] = {'value': {} }
    
    init['custom']['value']['django_user_unique'] = secret_id_for_user(user)

    init['merchant_key'] = {'value': settings.SAMURAI_CREDENTIALS.merchant_key}

    if update_url:
        init['redirect_url'] = {'value': base_url + reverse('samurai-update-payment-method-redirect')}
    else:
        init['redirect_url'] = {'value': base_url + reverse('samurai-new-payment-method-redirect')}

    init['custom']['value'] = json.dumps(init['custom']['value'])

    init['card_number'] = {}
    init['verification_value'] = {}

    if payment_method:
        if payment_method.last_four_digits:
            init['card_number']['value'] = "*" * 12 + payment_method.last_four_digits
            init['verification_value']['value'] = "*" * 3
        if not payment_method.is_sensitive_data_valid:
            init['verification_value']['error'] = "Your credit card number or security code are invalid"
            init['card_number']['error'] = init['verification_value']['error']

        if payment_method.last_transaction_error:
            # we only find this out after a failed transaction.
            init['non_field_error'] = "There was an error with your information. Please look it over carefully and try again."

    return init
