This is the python library for the [Samurai API](http://feefighters.com/samurai) from [Fee Fighters](http://feefighters.com). It allows you easily store customer payment information, and create transactions, without having to ever worry about having their credit card number cross your server.

(README in progress)

# Overview

## Payment Method

This a set of credentials for making a credit card payment. It includes:

* __less sensitive data__ that you will have access to (name, address, credit card expiration date, etc)
* __more sensitive data__ that you won't have access to (credit card number and cvv)
* __the state of the payment method__ (is data valid, is payment method redacted, etc)

Each Payment Method is identified by a `payment_method_token`.

## Transaction

This is an action taken based on a payment method, and/or a previous transaction. There are a 5 different types of transactions.

* __purchase__ - a complete payment
* __authorize__ - the first part of a two-step payment
* __capture__ - the second part of a two-step payment
* __void__ - the cancelation of any previous payment
* __credit__ - a partial or complete refund on an existing completed payment

Each Transaction is identified by a `reference_id`, and each set of transactions that relate to each other (the capture for an earlier authorize, the void of an earlier purchase, etc) is identified by a `transaction_token`.

# Installation

This library currently isn't a proper Python package, so you will have to get the source. The main directory serves as a module, though you should rename it to something like `samurai_client_python`, since dashes aren't valid for module names. The directory also works as a Django application, if you would like to use it for that.

# Core 

The module `samurai_client_python.core` and the file _transparent_redirect.html.example_ contain everything necessary to use the Samurai API. You will be in charge of saving references to Payment Methods and Transactions [Read More](/FeeFighters/samurai-client-python/blob/master/docs/core.md)

# Django

The modules `samurai_client_python.models`, `samurai_client_python.urls`, `samurai_client_python.views` make up a Django app which call on `samurai_client_python.core`. [Read More](/FeeFighters/samurai-client-python/blob/master/docs/core.md) (Though read first about Core, above)
