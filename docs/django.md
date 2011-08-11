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

