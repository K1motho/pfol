import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from decouple import config  # for .env

class EventbriteProxyView(APIView):
    permission_classes = [AllowAny]  # Allow public access from frontend

    def get(self, request):
        location = request.query_params.get('location', 'Nairobi')
        keyword = request.query_params.get('keyword', 'music')
        page = request.query_params.get('page', '1')

        PRIVATE_TOKEN = config('PREDICTHQ_PRIVATE_TOKEN')

        url = 'https://api.predicthq.com/v1/events/'

        headers = {
            'Authorization': f'Bearer {PRIVATE_TOKEN}'  # ✅ Use private token here
        }

        params = {
            'location.address': location,
            'q': keyword,
            'expand': 'venue,logo',
            'sort_by': 'date',
            'page': page,
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            
            # Debug prints:
            print("Request URL:", response.url)
            print("Response status code:", response.status_code)
            print("Response content:", response.text)

            response.raise_for_status()  # Will raise HTTPError for bad responses
            return Response(response.json())
        except requests.exceptions.RequestException as e:
            # Print the error details
            print("Request failed:", str(e))
            # If response exists, print response content
            if hasattr(e, 'response') and e.response is not None:
                print("Error response content:", e.response.text)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
