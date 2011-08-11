## Setup

In settings.py:

    import samurai_client_python.core as samurai

    SAMURAI_CREDENTIALS = samurai.FeeFighters(merchant_key = [your merchant key], merchant_password = [your merchant password])
    SAMURAI_SALT = # A randomly generated string
    SAMURAI_NEWMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error creating a new mayment method
    SAMURAI_NEWMETHOD_REDIRECT = # name of URL you want to redirect to upon success creating a new mayment method
    SAMURAI_UPDATEMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error updating a mayment method
    SAMURAI_UPDATEMETHOD_REDIRECT = # name of URL you want to redirect to upon success updating a mayment method

# Models

The Django models PaymentMethod and Transaction in `samurai_client_python.models` act very similarly to the classes of the same naem in `samurai_client_python.core`, but they have a couple key differences:

* The Django models don't fetch by default, you always have to call `fetch()` explicitly.
* You don't have to pass in the merchant key and password, though you do still have to pass in the processor_token each time because some users may choose to use multiple of those in the same system.
* Every significant action saves to the database. For instance:
 * When the redirect comes back, it will call a view to save the resulting Payment Method, if it's valid. (more on this view below)
 * purchase, authorize, capture, void, and credit will all add the resulting transaction to the database if successful

You shouldn't ever have to call `save()` on any of these models. Though, it is ok to delete them.

## Filtering

To get a particular payment method:

    PaymentMethod.objects.get(payment_method_token = payment_method_token)

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


To create a transparent redirect form.

    import samurai_client_python.views

    
    

how to use the trans_redir thing 



# Handling Redirects


test_credentials.py

    Django-authentication required. Django-South supported, migrations included.

