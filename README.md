This is the python library for the [Samurai API](http://feefighters.com/samurai) from [Fee Fighters](http://feefighters.com). It allows you easily store customer payment information, and create transactions, without having to ever worry about having their credit card number cross your server.

(README in progress)

## Overview

### Payment Method

This a set of credentials for making a credit card payment. It includes:

* __less sensitive data__ that you will have access to (name, address, credit card expiration date, etc)
* __more sensitive data__ that you won't have access to (credit card number and cvv)
* __the state of the payment method__ (is data valid, is payment method redacted, etc)

Each Payment Method is identified by a `payment_method_token`.

### Transaction

This is an action taken based on a payment method, and/or a previous transaction. There are a 5 different types of transactions.

* __purchase__ - a complete payment
* __authorize__ - the first part of a two-step payment
* __capture__ - the second part of a two-step payment
* __void__ - the cancelation of any previous payment
* __credit__ - a partial or complete refund on an existing completed payment

Each Transaction is identified by a `reference_id`, and each set of transactions that relate to each other (the capture for an earlier authorize, the void of an earlier purchase, etc) is identified by a `transaction_token`.

## Installation

This library currently isn't a proper Python package, so you will have to get the source. The main directory serves as a module, though you should rename it to something like `samurai_client_python`, since dashes aren't valid for module names. The directory also works as a Django application, if you would like to use it for that.

## Core

If you're just interested in using the API in a basic form, you should use `samurai_client_python.core`. It will allow you to create Payment Methods and Transactions.

### Transparent Redirect

First, you need to create a payment method, you first need to use something called a Transparent Redirect. This is a form you place on your website where your users enter all their credit card information. This form posts directly to FeeFighters, so, again, your server never sees the more sensitive parts. Feefighters will redirect your users to a url on your site (which you specify in a hidden field), with the payment_method_token of a newly created Payment Method in a GET variable. An example form, with all the necessary fields, can be found in the FeeFighters API documentation, or else you can look in [transparent_redirect.html.example](/FeeFighters/samurai-client-python/blob/master/transparent_redirect.html.example) in this repository.

### PaymentMethod

#### Create/Fetch

Now, you can create a PaymentMethod to get the information:

    from samurai_client_python.core import PaymentMethod

    payment_method = PaymentMethod(merchant_key = merchant_key, merchant_password = merchant_password,
        processor_token = processor_token, payment_method_token = payment_method_token)

This will create a PaymentMethod object based on the `payment_method_token` you pass in. You also have to have credentials for your merchant and processor ready. (If you don't have these, you should check with Fee Fighters.) This will fetch the information information from Fee Fighters right away. If you prefer to delay the fetch (since it hits the network and takes a second), you can supply the argument `do_fetch=False`, and call `fetch()` later:

    from samurai_client_python.core import PaymentMethod


    payment_method = PaymentMethod(merchant_key = merchant_key, merchant_password = merchant_password,
        processor_token = processor_token, payment_method_token = payment_method_token, do_fetch = False)

...

    payment_method.fetch()

Finally, you will probably end up having to supply the credentials in several places in your code, so you can cut down on repetition by creating a `FeeFighters` object first:

    feefighters = FeeFighters(merchant_key = merchant_key, merchant_password = merchant_password, processor_token = processor_token)

    payment_method = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token)

...

    payment_method_2 = PaymentMethod(feefighters = feefighters, payment_method_token = payment_method_token_2)

After a successful fetch, payment_method gets populated with the less sensitive information. You can access it directly, `payment_method.first_name` for instance. Integer fields will be converted to Python `int`s, and date fields will be converted to Python `datetime`s. Look at the Samurai documentation, and [core.py](/FeeFighters/samurai-client-python/blob/master/core.py) to see what fields get populated when you fetch. To test whether a fetch is successful, you can check if the `fetch()` function returns `True`, or if `payment_method_2.populated` is set to `True`.

If something went wrong, you should check `payment_method.errors`. For non-error info, check `payment_method.info`. It is a list of dictionaries, each being a message. The keys are `'context'`, `'key'` (which error/info message), and `'source'` (either 'samurai', 'gateway', or 'client' [generated by this client, not taken from over the network] )

    >>> print payment_method.errors
    [{'source': 'processor', 'key': 'country_not_supported', 'context': 'processor.avs'}, {'source': 'processor', 'key': 'too_short', 'context': 'input.cvv'}]

...

    >>> print payment_method.info
    [{'context':'processor.transaction', 'key':'success', 'source':'samurai'}]

You should also check `payment_method.is_sensitive_data_valid` (it may end up `False` without anything in the errors list). If it's false, it means something's wrong with either the credit card number or the cvv, in which case you should send the user back to the transparent redirect form. You should use the other fields in `payment_method` to pre-populate the form this time.

#### Update

If you want to change some of the less sensitive data (name, address, card expiration date, etc) you can do it directly. Just set the fields you want to change, and call `update()`. Also note that one of the fields is called "custom". This is for arbitrary data you would like FeeFighters to associate with the PaymentMethod. This client represents this field as a dictionary, and will convert it to JSON. Example:

    payment_method.expiry_year = 2020
    payment_method.last_name = "Johnson"
    payment_method.custom = {'a':'b'}

    payment_method.update()

...

Numerical data can be set as number, they will be converted into strings before saving. The DateTime fields (time updated, etc) cannot be updated. You should only put strings into the JSON field. (You can also put the custom information into a hidden field in the Transparent Redirect form if you json encode it first.)

#### Retain

If you decide to that a PaymentMethod is good to continue using for the long run, you should retain it:

    payment_method.retain()

#### Redact

If you have a PaymentMethod that you don't plan to use again, you should redact it:

    payment_method.redact()

### Transaction

#### Create/Fetch

To start a series of transactions, first create a Transaction object. It requires a PaymentMethod object. Similarly to PaymentMethod, it also requires your credentials, which you can supply explicitly, or use an existing FeeFighters object for shorthand:

    from samurai_client_python.core import Transaction

    transaction = Transaction(merchant_key = test_credentials.merchant_key, merchant_password = test_credentials.merchant_password,
                processor_token = test_credentials.processor_token, payment_method = payment_method, do_fetch = False)

or

    transaction = Transaction(feefighters = feefighters, payment_method = payment_method, 
        processor_token = processor_token, do_fetch = False)





## Django

The Django models are similar to the core objects. One key difference to remember is that they don't fetch by default, you have to call .fetch() explicitly.

In settings.py:

    import samurai_client_python.core as samurai

    SAMURAI_CREDENTIALS = samurai.FeeFighters(merchant_key = [your merchant key], merchant_password = [your merchant password])
    SAMURAI_SALT = # A randomly generated string
    SAMURAI_NEWMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error creating a new mayment method
    SAMURAI_NEWMETHOD_REDIRECT = # name of URL you want to redirect to upon success creating a new mayment method
    SAMURAI_UPDATEMETHOD_ERROR_REDIRECT = # name of URL you want to redirect to upon error updating a mayment method
    SAMURAI_UPDATEMETHOD_REDIRECT = # name of URL you want to redirect to upon success updating a mayment method


To create a transparent redirect form.

    import samurai_client_python.views

    
    

how to use the trans_redir thing 







How the views work:



test_credentials.py

    Django-authentication required. Django-South supported, migrations included.

## Testing

### Credentials

If you want any of the tests to pass, you will need to create a file called test_credentials.py

### Django

If you don't have this properly configured as part of Django, the Django tests will not pass.
