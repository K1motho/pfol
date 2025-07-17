from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import json, requests, datetime, base64

from django.contrib.auth import get_user_model
from .models import PaymentTransaction
from payments.utils.daraja import get_access_token

User = get_user_model()

def normalize_phone(phone: str) -> str:
    phone = str(phone).strip()
    if phone.startswith('07'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    return phone


@permission_classes([AllowAny])
class CheckoutView(APIView):
    def post(self, request):
        try:
            data = request.data
            print("Order received:", json.dumps(data, indent=2))
            # TODO: Save order or create payment intent logic here
            return Response({'message': 'Order received successfully'}, status=200)
        except Exception as e:
            print("Checkout Error:", str(e))
            return Response({'error': 'Invalid data'}, status=400)


@permission_classes([AllowAny])
class InitiateStkPushView(APIView):
    def post(self, request):
        try:
            phone = normalize_phone(request.data.get('phone'))
            amount = int(request.data.get('amount', 0))

            if not phone or amount <= 0:
                return Response({'error': 'Phone number and positive amount are required'}, status=400)

            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shortcode = '174379'  # Use your shortcode here
            passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  # Use your passkey here
            password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()

            payload = {
                "BusinessShortCode": shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone,
                "PartyB": shortcode,
                "PhoneNumber": phone,
                "CallBackURL": "https://yourdomain.com/api/payments/mpesa-callback/",
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
            print("STK Push Error:", str(e))
            return Response({'error': 'Failed to initiate payment'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        try:
            body = request.data
            print("M-Pesa Callback received:", json.dumps(body, indent=2))

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
            print("Callback Error:", str(e))
            return Response({'error': 'Invalid callback data'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class UserTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

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
