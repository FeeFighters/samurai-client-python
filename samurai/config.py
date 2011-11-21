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
import sys
import logging
from logging import Formatter, StreamHandler

debug = False
# FIXME: Leaving it here for dev. To be removed.
merchant_key = 'edfd1670f11055730dca8219'
merchant_password = '43cc06e733c8f9135c331b78'
processor_token = 'a799d7691f7c5b492751b34e'

top_uri='https://api.samurai.feefighters.com/v1/',

log_format = '%(levelname)s - %(asctime)s - %(filename)s:%(funcName)s:%(lineno)s - \n%(message)s\n\n'
def default_logger():
    """
    Returns an instance of default logger.
    Default logger dumps data to `sys.stderr`.
    """
    logger = logging.getLogger('samurai')
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler(sys.stderr)
    handler.setFormatter(Formatter(log_format))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

logger = default_logger()
