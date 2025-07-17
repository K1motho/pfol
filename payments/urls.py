from django.urls import path
from .views import (
    StripeCreatePaymentIntentView,
    InitiateStkPushView,
    MpesaCallbackView,
    UserTransactionsView,
)

urlpatterns = [
    path('payment/create-payment-intent/', StripeCreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('payment/initiate-stk-push/', InitiateStkPushView.as_view(), name='initiate-stk-push'),
    path('payment/mpesa-callback/', MpesaCallbackView.as_view(), name='mpesa-callback'),
    path('payment/user-transactions/', UserTransactionsView.as_view(), name='user-transactions'),
]
