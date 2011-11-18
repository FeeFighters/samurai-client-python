"""
    Configs for Samurai API.
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Set samurai api configurations on this module.

    Import this module and set the `merchant_key` and `merchant_password`.
    Other modules use the configuration set on this object.
    ::
        import samurai.config as config
        config.merchant_key = your_merchant_key
        config.merchant_password = your_merchant_password
"""
merchant_key = None
merchant_password = None
top_uri='https://api.samurai.feefighters.com/v1/',
