from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import datetime
import base64
from decouple import config
import stripe

from django.contrib.auth import get_user_model
from .models import PaymentTransaction
from payments.utils.daraja import get_access_token

User = get_user_model()

# Load config variables
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')

MPESA_SHORTCODE = config('MPESA_SHORTCODE')
MPESA_PASSKEY = config('PASS_KEY')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL')
          
# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY


def normalize_phone(phone: str) -> str:
    phone = str(phone).strip()
    if phone.startswith('07'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    return phone


@permission_classes([AllowAny])
class StripeCreatePaymentIntentView(APIView):
    def post(self, request):
        try:
            amount = request.data.get('amount')
            currency = request.data.get('currency', 'KES').lower()  # default KES

            if not amount:
                return Response({'error': 'Amount is required'}, status=400)

            # Stripe expects amount in the smallest currency unit (e.g. cents)
            # For KES, which has no decimals, multiply by 100 to convert to cents-like unit
            amount_in_smallest_unit = int(float(amount) * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_in_smallest_unit,
                currency=currency,
                payment_method_types=["card"],
            )

            return Response({
                'clientSecret': intent.client_secret,
                'publishableKey': STRIPE_PUBLISHABLE_KEY,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@permission_classes([AllowAny])
class InitiateStkPushView(APIView):
    def post(self, request):
        try:
            phone = normalize_phone(request.data.get('phone'))
            amount = int(request.data.get('amount', 0))

            if not phone or amount <= 0:
                return Response({'error': 'Phone number and positive amount are required'}, status=400)

            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f'{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}'.encode()).decode()

            payload = {
                "BusinessShortCode": MPESA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone,
                "PartyB": MPESA_SHORTCODE,
                "PhoneNumber": phone,
                "CallBackURL": MPESA_CALLBACK_URL,
                "AccountReference": "WapiNaLiniTicket",
                "TransactionDesc": "Wapi Na Lini Ticket Payment"
            }

            token = get_access_token()
            if not token:
                return Response({'error': 'Failed to retrieve access token'}, status=500)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            mpesa_response = requests.post(
                'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers=headers,
                timeout=30
            )

            return Response(mpesa_response.json())

        except Exception as e:
            return Response({'error': 'Failed to initiate payment', 'details': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        try:
            body = request.data
            stk = body.get('Body', {}).get('stkCallback', {})
            result_code = stk.get('ResultCode')
            result_desc = stk.get('ResultDesc')
            checkout_request_id = stk.get('CheckoutRequestID')
            metadata = stk.get('CallbackMetadata', {}).get('Item', [])

            transaction_data = {item['Name']: item.get('Value') for item in metadata}

            phone = normalize_phone(transaction_data.get('PhoneNumber'))
            matched_user = User.objects.filter(phone=phone).first()  # Adjust if phone stored differently

            PaymentTransaction.objects.create(
                user=matched_user,
                phone=phone,
                amount=transaction_data.get('Amount', 0),
                transaction_id=transaction_data.get('MpesaReceiptNumber') or f"FAILED-{checkout_request_id}",
                checkout_request_id=checkout_request_id,
                result_code=result_code,
                result_description=result_desc
            )

            if result_code == 0:
                return Response({'message': 'Payment successful'})
            else:
                return Response({'message': 'Payment failed', 'description': result_desc})

        except Exception as e:
            return Response({'error': 'Invalid callback data', 'details': str(e)}, status=400)


@permission_classes([IsAuthenticated])
class UserTransactionsView(APIView):
    def get(self, request):
        transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-timestamp')
        data = [
            {
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "phone": tx.phone,
                "date": tx.timestamp.strftime('%Y-%m-%d %H:%M'),
                "status": "Success" if tx.result_code == 0 else "Failed"
            }
            for tx in transactions
        ]
        return Response({"transactions": data})
