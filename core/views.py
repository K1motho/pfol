import requests
from decouple import config
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .serializers import RegisterSerializer, UserSerializer, FriendEventSerializer, MessageSerializer, NotificationSerializer
from .models import User, Friendship, AttendedEvent,  Message, Notification
from .utils import send_otp_email
from django.db.models import Q

User = get_user_model()

class DiscoverEventsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        keyword = request.query_params.get("keyword", "music")
        location = request.query_params.get("location", "Nairobi")
        size = request.query_params.get("size", 10)

        TICKETMASTER_API_KEY = config("TICKETMASTER_API_KEY")

        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "keyword": keyword,
            "city": location,
            "size": size
        }

        try:
            res = requests.get(url, params=params)
            data = res.json()

            if "_embedded" in data and "events" in data["_embedded"]:
                events = data["_embedded"]["events"]
                return Response(events)

            return Response({"detail": "No events found."}, status=404)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Token is required'}, status=400)

        try:
            CLIENT_ID = config("GOOGLE_CLIENT_ID")
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)

            email = idinfo.get('email')
            name = idinfo.get('name')

            if not email:
                return Response({'detail': 'Google token missing email'}, status=400)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email.split('@')[0], 'first_name': name}
            )

            send_otp_email(email)

            return Response({
                'email': email,
            })

        except ValueError:
            return Response({'detail': 'Invalid Google token'}, status=400)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()


class CheckUsernameView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.query_params.get('username', '').strip()
        if not username:
            return Response({'available': False, 'error': 'No username provided'}, status=400)
        is_available = not User.objects.filter(username=username).exists()
        return Response({'available': is_available})


class CheckEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get('email', '').strip()
        if not email:
            return Response({'available': False, 'error': 'No email provided'}, status=400)
        is_available = not User.objects.filter(email=email).exists()
        return Response({'available': is_available})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FriendListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friends = []
        for f in friendships:
            friend = f.user2 if f.user1 == user else f.user1
            friends.append(friend)
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)


class FriendEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friend_ids = [f.user2.id if f.user1 == user else f.user1.id for f in friendships]
        events = AttendedEvent.objects.filter(user__id__in=friend_ids).order_by('-attended_at')
        data = [
            {
                "id": event.event_id,
                "name": event.title,
                "date": event.date,
                "image_url": event.image_url
            } for event in events
        ]
        serializer = FriendEventSerializer(data, many=True)
        return Response(serializer.data)


class FriendProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, friend_id):
        user = request.user
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "Friend not found."}, status=404)

        is_friend = Friendship.objects.filter(
            (Q(user1=user) & Q(user2=friend)) | (Q(user1=friend) & Q(user2=user))
        ).exists()

        if not is_friend:
            return Response({"error": "Not friends."}, status=403)

        user_event_ids = set(
            AttendedEvent.objects.filter(user=user).values_list('event_id', flat=True)
        )
        friend_events = AttendedEvent.objects.filter(user=friend, event_id__in=user_event_ids)
        mutual = [
            {
                "id": e.event_id,
                "name": e.title,
                "date": e.date,
                "image_url": e.image_url
            } for e in friend_events
        ]

        data = UserSerializer(friend).data
        data['mutual_events'] = mutual
        return Response(data)

class MessageListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, friend_id):
        user = request.user
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "Friend not found"}, status=404)

        is_friend = Friendship.objects.filter(
            (Q(user1=user) & Q(user2=friend)) | (Q(user1=friend) & Q(user2=user))
        ).exists()
        if not is_friend:
            return Response({"error": "Not friends."}, status=403)

        messages = Message.objects.filter(
            (Q(sender=user) & Q(receiver=friend)) | (Q(sender=friend) & Q(receiver=user))
        ).order_by('timestamp')

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, friend_id):
        user = request.user
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "Friend not found"}, status=404)

        is_friend = Friendship.objects.filter(
            (Q(user1=user) & Q(user2=friend)) | (Q(user1=friend) & Q(user2=user))
        ).exists()
        if not is_friend:
            return Response({"error": "Not friends."}, status=403)

        content = request.data.get('content')
        if not content:
            return Response({"error": "Message content is required."}, status=400)

        message = Message.objects.create(sender=user, receiver=friend, content=content)
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=201)
    
class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user).order_by('-timestamp')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)