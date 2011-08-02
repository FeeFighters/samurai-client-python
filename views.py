
def new_payment_method_redirect(request):
    new_method = PaymentMethod(payment_method_token = request.GET['payment_method_token'])

    try:
        new_method.full_clean()
        new_method.save()
        return get_view_by_string(settings.FEEFIGHTER_NEWMETHOD_REDIRECT) # somehow django's url thing resolves strings into views. we'll do that
    except ValidationError: # not attached to the right user
        return get_view_by_string(settings.FEEFIGHTER_NEWMETHOD_ERROR_REDIRECT)

def update_payment_method_redirect(request):
    new_method = PaymentMethod(payment_method_token = request.GET['payment_method_token'])

    try:
        new_method.full_clean()
        old_method = PaymentMethod.objects.get(payment_method_token = method.custom['django_prev_payment_method_token'])
        old_method.redact()
        old_method.delete()
        new_method.save()
        return get_view_by_string(settings.FEEFIGHTER_UPDATEMETHOD_REDIRECT)
    except ValidationError: # not attached to the right user
        return get_view_by_string(settings.FEEFIGHTER_UPDATEMETHOD_ERROR_REDIRECT)

