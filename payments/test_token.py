import requests
import base64

consumer_key = "e5eRBfIE4Y1Q7NH1tNRYiITVM0JMZTaWGseqzXkRl5hk1mY8kFnbVbs2lAK1Rndb"
consumer_secret = "ILQxtkdg9ZDOEuTRdKDbTPUsYmQBrDJvvn21lyCTU1zcrCCT"

credentials = f"{consumer_key}:{consumer_secret}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    "Authorization": f"Basic {encoded_credentials}"
}

url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
