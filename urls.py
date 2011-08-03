from django.conf.urls.defaults import *
from views import  new_payment_method_redirect, update_payment_method_redirect

urlpatterns = patterns('',
    url(r'^new_payment_info$', new_payment_method_redirect, name='samurai-new-payment-method-redirect'),
    url(r'^update_payment_info$', update_payment_method_redirect, name='samurai-update-payment-method-redirect'),
)
