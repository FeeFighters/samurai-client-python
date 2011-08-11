This is the python library for the [Samurai API](http://feefighters.com/samurai) from [Fee Fighters](http://feefighters.com). It allows you easily store customer payment information, and create transactions, without having to ever worry about having their credit card number cross your server.

(README in progress)

## Overview

### Payment Method

This a set of credentials for making a credit card payment. It includes:

* less-sensitive data that you will have access to (name, address, etc)
* more sensitive data that you won't have access to (credit card number and cvv)
* the state of the payment method (is data valid, is payment method redacted, etc).

Each Payment Method is identified by a `payment_method_token`.

### Transaction

This is an action taken based on a payment method, and/or a previous transaction. There are a 5 different types of transactions.

* _purchase_ - a complete payment
* _authorize_ - the first part of a two-step payment
* _capture_ - the second part of a two-step payment
* _void_ - the cancelation of any previous payment
* _credit_ - a partial or complete refund on an existing completed payment

Each Transaction is identified by a `reference_id`, and each set of transactions that relate to each other (the capture for an earlier authorize, the void of an earlier purchase, etc) is identified by a `transaction_token`.

## Installation

This library currently isn't a proper Python module, so you will have to get the source. The main directory serves as a module. It also serves as a Django app, if you're interested in that.

You should rename the directory to something like samurai_client_python so you can import it.

## Core

If you're just interested in using the API in a basic form, you should use the library's core. It will allow you to take a 

## Django


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
