import requests
import base64
import time
from decouple import config



CONSUMER_KEY = config('CONSUMER_KEY')
CONSUMER_SECRET = config('CONSUMER_SECRET')

cached_token = None
token_expiry = 0

def get_access_token():
    global cached_token, token_expiry

    current_time = time.time()
    if cached_token and current_time < token_expiry:
        return cached_token

    try:
        credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}"
        }

        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = int(token_data.get('expires_in'))

            cached_token = access_token
            token_expiry = current_time + expires_in - 60
            return access_token
        else:
            print("Token Error:", response.text)
            return None

    except Exception as e:
        print("Access Token Exception:", str(e))
        return None