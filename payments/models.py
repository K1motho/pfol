from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentTransaction(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('stripe', 'Stripe'),
        ('mpesa', 'M-Pesa'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # Optional for Stripe payments
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='KES')  # currency, default Kenyan Shillings

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)

    # Stripe-specific fields
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    # M-Pesa-specific fields
    transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)

    # Common result/status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_description = models.TextField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.payment_method} - {self.status}"
