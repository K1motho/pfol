from django.urls import path
from . import views
from .views import UserTransactionsView

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('initiate_stk_push/', views.initiate_stk_push, name='initiate_stk_push'),
    path('payments/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('process_payment/', views.process_payment),
    path('create_payment/', views.create_payment),
    path('user-transactions/', UserTransactionsView.as_view(), name='user-transactions'),

]