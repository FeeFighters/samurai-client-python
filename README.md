This is the python library for the [Samurai API](http://feefighters.com/samurai) from [Fee Fighters](http://feefighters.com). It allows you easily store customer payment information, and create transactions, without having to ever worry about having their credit card number cross your server.

(README in progress)

## Overview

### Payment Method

This a set of credentials for making a credit card payment. It includes:

* __less sensitive data__ that you will have access to (name, address, etc)
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

First, you need to create a payment method, you first need to use something called a Transparent Redirect. This is a form you place on your website where your users enter all their credit card information. This form posts directly to FeeFighters, so, again, your server never sees the more sensitive parts. Feefighters will redirect your users to a url on your site (which you specify in a hidden field), with the payment_method_token of a newly created Payment Method in a GET variable. An example form, with all the necessary fields, can be found in the FeeFighters API documentation, or else you can look in [transparent_redirect.html.example](/FeeFighters/samurai-client-python/blob/master/transparent_redirect.html.example) in this repository.

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
