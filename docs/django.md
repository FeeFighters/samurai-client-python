# Setup

* Django-South is supported, with migrations included.
* Django-authentication is required.

In settings.py:

    import samurai_client_python.core as samurai

    SAMURAI_CREDENTIALS = samurai.FeeFighters(merchant_key = [your merchant key], merchant_password = [your merchant password])
    SAMURAI_SALT = # A randomly generated string. You can use: User.objects.make_random_password(32, string.digits + string.letters)
    SAMURAI_NEWMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error creating a new mayment method
    SAMURAI_NEWMETHOD_REDIRECT = # name of URL you want to redirect to upon success creating a new mayment method
    SAMURAI_UPDATEMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error updating a mayment method
    SAMURAI_UPDATEMETHOD_REDIRECT = # name of URL you want to redirect to upon success updating a mayment method

In urls.py:

You need to route the samurai views to any base URL of your choosing:

    (r'^payment/', include('samurai_client_python.urls')),

In this example, we will route it to "/payment/...". The app will take care of the rest.

# Models

The Django models PaymentMethod and Transaction in `samurai_client_python.models` act very similarly to the classes of the same naem in `samurai_client_python.core`, but they have a couple key differences:

* The Django models don't fetch by default, you always have to call `fetch()` explicitly.
* You don't have to pass in the merchant key and password, though you do still have to pass in the processor_token each time because some users may choose to use multiple of those in the same system.
* Every significant action saves to the database. For instance:
 * When the redirect comes back, it will call a view to save the resulting Payment Method, if it's valid. (more on this view below)
 * purchase, authorize, capture, void, and credit will all add the resulting transaction to the database if successful
* calling full_clean() on a PaymentMethod will confirm that the payment method was set up to be attached to the logged in user (via a hashed version of their user ID added when the user submitted the data). This is mainly done by the supplied views, but you can also do this to check on a payment_method you create (even if you don't save).

You shouldn't ever have to call `save()` on any of these models. Though, it is ok to delete them.

## Filtering

Some useful ways to access the data:

To get a particular payment method:

    PaymentMethod.objects.get(payment_method_token = payment_method_token, user = request.user, disabled = False)

Note that you should probably always pass the user into the query, to prevent somebody from hijacking somebody else's PaymentMethod.

To get a particular transaction:

    Transaction.objects.get(reference_id = reference_id)

To get all transactions associated with a given transaction (the authorize and capture for a void you just did, for instance):

    Transaction.objects.filter(transaction_token = void_transaction.transaction_token)

To get a specific transaction associated with a different transaction (the capture for a void you just did, for instance):

    Transaction.objects.filter(transaction_token = void_transaction.transaction_token, transaction_type = "capture")

To get all transactions for a payment method:

    Transaction.objects.filter(payment_method = payment_method)


# Views

## Transparent Redirect Form

Again, this is the form that you create that will redirect your users directly to FeeFighters. First, you should put the form into a template. Unfortunately, we can't use Django forms for this because the names of the fields that FeeFighters expect contain brackets, so (as far as I know) there's no nice way to set them properly with Django. So we have to put them into a template manually. A working example form can be found at: [transparent_redirect.html.example](/FeeFighters/samurai-client-python/blob/master/transparent_redirect.html.example). You'll notice that it contains reference to something called `samurai_form`.

To create an empty transparent redirect form:

    from samurai_client_python.views import get_transparent_redirect_form_initial

    samurai_form = get_transparent_redirect_form_initial(request.user, settings.BASE_URL)

    return render_to_response('template/path.html', {'samurai_form':samurai_form }, context_instance=RequestContext(request))

(The name 'samurai_form' is just an example, which coincides with the example in transparent_redirect.html.example) This will fill in the necessary credentials. It will also add a hashed (using the salt you supply) version of the user's id. That way, when it comes back, the (supplied) view can verify that the recipient is the intended one before saving the payment method.

Now, supposing you have an existing payment method, and you want to create a form for the user to update it (supposing the credit card number was bad). You can do the following:

To create a transparent redirect form pre-populated from an existing Payment Method in the database:

    from samurai_client_python.views import get_transparent_redirect_form_initial

    if PaymentMethod.objects.filter(payment_method_token = request.GET['old_payment_method_token'], disabled = False).exists():
        old_payment_method = PaymentMethod.objects.get(payment_method_token = request.GET['old_payment_method_token'], disabled = False)
        old_payment_method.fetch()

        # the True is for "update". it will add a reference to this payment_method_token, so we know to replace it if the
        # payment method resulting from this form is good data.
        samurai_form = get_transparent_redirect_form_initial(request.user, settings.BASE_URL, old_payment_method, True) 

Now, supposing the user entered malformed data, thus the token hasn't been saved. You can still get the token (see below for details). You can still use it to pre-populate the transparent redirect form:

    # user required for security measure, don't save this, however
    old_payment_method = PaymentMethod(payment_method_token = request.GET['old_payment_method_token'], user = request.user)
    old_payment_method.fetch()
    old_payment_method.full_clean() # handle the exception however you wish

    # not passing it True for "update", however it is safe to do so if you want, for reasons laid out below:
    samurai_form = get_transparent_redirect_form_initial(request.user, settings.BASE_URL, old_payment_method)

    return render_to_response('template/path.html', {'samurai_form':samurai_form }, context_instance=RequestContext(request))
   
Finally, supposing you have an existing payment method that you want to update. You create a transparent redirect form, and the user puts in bad data. So you have a payment method that doesn't get saved because of the bad data, and yet it's set to replace the original payment method. In this case you can still pass it in as before:

    bad_payment_method = PaymentMethod(payment_method_token = request.GET['bad_payment_method_token'], user = request.user)
    bad_payment_method.fetch()
    bad_payment_method.full_clean() # handle the exception however you wish

    # passing in True for update. It will know to replace the older payment method.
    samurai_form = get_transparent_redirect_form_initial(request.user, settings.BASE_URL, bad_payment_method, True)

    return render_to_response('template/path.html', {'samurai_form':samurai_form }, context_instance=RequestContext(request))

Passing in True for update is always safe to do. If the payment method is in the database, it will set the form up to update that payment method. If the payment method is not in the database, it will check to see if that payment method is a failed attempt at replacing another payment method (as in our example here). If so, it will set the form up to replace the same payment method it was replacing (and this can continue through indefinite failed attempts). If the payment method is neither in the database, nor set up to replace another payment method that is in the database, the update flag is ignored.

Note that if a payment\_method and True for update are passed into `get_transparent_redirect_form_initial`, Samurai will use the values submitted in the previous payment\_method for every required field that is submitted as blank in the new form. In addition, the same applies to credit card number and CVV if they are invalid, which means it's safe to populate the fields with the unknown digits replaced by `*` characters. The `*` characters would make it invalid, thus the previous values would be used. For convenience, in the template `samurai_form.card_number.value` (samurai\_form being the example template variable holding the form values, yours may be different) and `samurai_form.verification_value` will hold the appropriate values with the unknown digits replaced by `*` characters.

Finally, note that this form will pass in error messages for fields with errors, and . At this time there's no convenent way to override the messages with your own error messages, but they're found at `samurai_form['field_name']['error']` if you wanted to try to replace them. There's also a `samurai_form['non_field_error']`.

# Handling Redirects

When a user is redirected back from FeeFighters, they are sent to the URL we send them. The transparent redirect form we set up (above) will tell FeeFighters to send the user to an appropriate view that is included as part of this app. This view will verify that the credit card number and cvv were not malformed (though it can't verify that the numbers are correct before making a transaction).

If this is a new payment method, it will create the new `PaymentMethod` to the database, retain it, and forward the user once again, to SAMURAI_NEWMETHOD_REDIRECT if the data looks good and there are no errros, and SAMURAI_NEWMETHOD_ERROR_REDIRECT if there are problems.

If this is an updated payment method (get_transparent_redirect_form_initial was called with update=True, and the payment method was set up to replace an existing payment method in the database), it will create the new `PaymentMethod`, retain it, redact the `PaymentMethod` it is replacing, and set its disabled field to True. This is instead of deleting, so Django won't delete any associated Transactions, or anything else you may have pointing to it. If your users have multiple payment methods associated with them, you should filter for disabled=False when you want to pull up active ones. You can also prune it by deleting disabled PaymentMethods, but again be careful about deleting associated Transactions and other objects.

The views that these will forward to are up to you to create. The `payment_method_token` will be passed in as a GET variable. You may choose to have the UPDATE and NEW views point to the same place. You may want to create a transaction and peform a purchase. If transaction.purchase() returns False, you may want to send the user back to the form again, and set it up prepopulate the form and update the old payment method. See the above examples.

For the ERROR views, you may want to send the user back to the old form, prepopulated as well. You should create a new PaymentMethod object (without saving it), call full_clean() to make sure it was created by the correct user, and pass it to transparent_redirect_form_initial. See the above examples.
