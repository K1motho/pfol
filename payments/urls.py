from django.urls import path
from .views import (
    StripeCreatePaymentIntentView,
    InitiateStkPushView,
    MpesaCallbackView,
    UserTransactionsView,
)

urlpatterns = [
    path('payments/initiate/', InitiateStkPushView.as_view(), name='initiate-stk-push'),
    path('payments/create-payment-intent/', StripeCreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('payments/mpesa-callback/', MpesaCallbackView.as_view(), name='mpesa-callback'),
    path('payments/user-transactions/', UserTransactionsView.as_view(), name='user-transactions'),
]
