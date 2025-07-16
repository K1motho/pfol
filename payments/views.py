from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

import json, requests, datetime, base64
from payments.utils.daraja import get_access_token
from .models import PaymentTransaction

User = get_user_model()

def normalize_phone(phone):
    phone = str(phone).strip()
    if phone.startswith('07'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    return phone

@csrf_exempt
def checkout_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Order received:", json.dumps(data, indent=2))
            return JsonResponse({'message': 'Order received successfully'}, status=200)
        except Exception as e:
            print("Checkout Error:", str(e))
            return JsonResponse({'error': 'Invalid data'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def initiate_stk_push(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        body = json.loads(request.body)
        phone = normalize_phone(body.get('phone'))
        amount = int(body.get('amount'))

        if not phone or not amount:
            return JsonResponse({'error': 'Phone number and amount are required'}, status=400)

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        shortcode = '174379'
        passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
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
            "CallBackURL": "https://yourdomain.com/api/payments/callback/",
            "AccountReference": "CymanOrder",
            "TransactionDesc": "Cyman Wear Payment"
        }

        token = get_access_token()
        if not token:
            return JsonResponse({'error': 'Failed to retrieve access token'}, status=500)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers
        )

        return JsonResponse(response.json())

    except Exception as e:
        print("STK Push Error:", str(e))
        return JsonResponse({'error': 'Failed to initiate payment'}, status=500)

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            print("M-Pesa Callback received:", json.dumps(body, indent=2))

            stk = body.get('Body', {}).get('stkCallback', {})
            result_code = stk.get('ResultCode')
            result_desc = stk.get('ResultDesc')
            checkout_request_id = stk.get('CheckoutRequestID')
            metadata = stk.get('CallbackMetadata', {}).get('Item', [])
            transaction_data = {item['Name']: item.get('Value') for item in metadata}

            phone = normalize_phone(transaction_data.get('PhoneNumber'))
            matched_user = User.objects.filter(phone=phone).first()  # Adjust if using Profile

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
                return JsonResponse({'message': 'Payment successful'})
            else:
                return JsonResponse({'message': 'Payment failed', 'description': result_desc})

        except Exception as e:
            print("Callback Error:", str(e))
            return JsonResponse({'error': 'Invalid callback data'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UserTransactionsView(View):
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
        return JsonResponse({"transactions": data}, status=200)

@csrf_exempt
def process_payment(request):
    return JsonResponse({'message': 'Process payment placeholder'})

@csrf_exempt
def create_payment(request):
    return JsonResponse({'message': 'Stripe simulation placeholder'})