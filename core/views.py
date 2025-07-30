import requests
from decouple import config
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.shortcuts import get_object_or_404
from django.db.models import Q

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    FriendEventSerializer,
    FriendRequestSerializer,
    MessageSerializer,
    NotificationSerializer,
    InvitationSerializer,
    AttendedEventSerializer, CustomTokenObtainPairSerializer
)
from .models import User, Friendship, FriendRequest, AttendedEvent, Message, Notification, Invitation
from .utils import send_otp_email

User = get_user_model()

# ------------------- Password Reset Views ----------------------

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "If an account with that email exists, a reset link has been sent."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = config('FRONT_END_URL')
        reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Wapi Na Lini Password Reset",
            message=f"Hello,\n\nTo reset your password, click the link below:\n\n{reset_url}\n\nIf you didn't request this, ignore this email.",
            from_email=None,
            recipient_list=[user.email],
        )

        return Response({"message": "If an account with that email exists, a reset link has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({"message": "Password has been reset successfully."})

# ------------------- Event Discovery ----------------------

class DiscoverEventsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        keyword = request.query_params.get("keyword", "music")
        location = request.query_params.get("location", "Nairobi")
        size = request.query_params.get("size", 10)
        TICKETMASTER_API_KEY = config("TICKETMASTER_API_KEY")
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {"apikey": TICKETMASTER_API_KEY, "keyword": keyword, "city": location, "size": size}

        try:
            res = requests.get(url, params=params)
            data = res.json()
            if "_embedded" in data and "events" in data["_embedded"]:
                return Response(data["_embedded"]["events"])
            return Response({"detail": "No events found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ------------------- Authentication and Registration ----------------------

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
            return Response({'email': email})
        except ValueError:
            return Response({'detail': 'Invalid Google token'}, status=400)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.save()

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

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
        print("✅ CheckEmailView accessed")
        email = request.query_params.get('email', '').strip()
        if not email:
            print("❌ No email provided")
            return Response({'available': False, 'error': 'No email provided'}, status=400)
        is_available = not User.objects.filter(email=email).exists()
        print(f"📧 Email checked: {email} | Available: {is_available}")


        return Response({'available': is_available})

# ------------------- User Profile ----------------------

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

# ------------------- User Search ----------------------

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

# ------------------- Friend Requests ----------------------

class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return list of friend requests sent by the current user
        friend_requests = FriendRequest.objects.filter(sender=request.user, status='pending')
        serializer = FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        receiver_id = request.data.get('receiver')
        if not receiver_id:
            return Response({'error': 'Receiver ID is required'}, status=400)

        if int(receiver_id) == request.user.id:
            return Response({'error': 'You cannot send a friend request to yourself'}, status=400)

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'Receiver not found'}, status=404)

        if FriendRequest.objects.filter(sender=request.user, receiver=receiver, status='pending').exists():
            return Response({'error': 'Friend request already sent'}, status=400)

        friend_request = FriendRequest.objects.create(
            sender=request.user,
            receiver=receiver,
            status='pending'
        )

        # ✅ Create a notification for the receiver
        Notification.objects.create(
            recipient=receiver,
            sender=request.user,
            type='friend_request',
            content=f"{request.user.username} sent you a friend request."
        )

        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=201)

    def delete(self, request, receiver_id=None):
        if not receiver_id:
            return Response({'error': 'Receiver ID is required in the URL'}, status=400)

        try:
            friend_request = FriendRequest.objects.get(
                sender=request.user,
                receiver__id=receiver_id,
                status='pending'
            )
            friend_request.delete()
            return Response({'message': 'Friend request canceled'}, status=200)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'No pending request to cancel'}, status=404)

        
class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sender_id = request.data.get('sender_id')
        print("➡️ AcceptFriendRequestView called with sender_id:", sender_id)

        if not sender_id:
            return Response({'error': 'Sender ID is required'}, status=400)

        try:
            friend_request = FriendRequest.objects.get(
                sender__id=sender_id,
                receiver=request.user,
                status='pending'
            )

            # Create friendship both ways or however your model works
            Friendship.objects.create(user1=friend_request.sender, user2=request.user)

            # Delete friend request after creating friendship
            friend_request.delete()

            # Delete original friend request notification
            Notification.objects.filter(
                recipient=request.user,
                sender__id=sender_id,
                type='friend_request'
            ).delete()

            # Create notification to inform sender
            Notification.objects.create(
                recipient=friend_request.sender,
                sender=request.user,
                type='friend_request_accepted',
                content=f"{request.user.username} accepted your friend request."
            )

            return Response({'message': 'Friend request accepted'}, status=200)

        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=404)

        except Exception as e:
            print("🔥 Error in AcceptFriendRequestView:", str(e))
            return Response({'error': str(e)}, status=500)

class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sender_id = request.data.get('sender_id')
        print("➡️ RejectFriendRequestView called with sender_id:", sender_id)

        if not sender_id:
            return Response({'error': 'Sender ID is required'}, status=400)

        try:
            friend_request = FriendRequest.objects.get(
                sender__id=sender_id,
                receiver=request.user,
                status='pending'
            )

            # Delete the friend request entirely
            friend_request.delete()

            # Delete the original friend request notification
            Notification.objects.filter(
                recipient=request.user,
                sender__id=sender_id,
                type='friend_request'
            ).delete()

            return Response({'message': 'Friend request rejected'}, status=200)

        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=404)

        except Exception as e:
            print("🔥 Error in RejectFriendRequestView:", str(e))
            return Response({'error': str(e)}, status=500)

# ------------------- Friends and Invitations ----------------------

class FriendListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friends = [f.user2 if f.user1 == user else f.user1 for f in friendships]
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)

class FriendEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friend_ids = [f.user2.id if f.user1 == user else f.user1.id for f in friendships]
        events = AttendedEvent.objects.filter(user__id__in=friend_ids).order_by('-attended_at')
        data = [{
            "id": event.event_id,
            "name": event.title,
            "date": event.date,
            "image_url": event.image_url
        } for event in events]
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
        mutual = [{
            "id": e.event_id,
            "name": e.title,
            "date": e.date,
            "image_url": e.image_url
        } for e in friend_events]

        data = UserSerializer(friend).data
        data['mutual_events'] = mutual
        return Response(data)

# ------------------- Messages ----------------------

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

# ------------------- Notifications ----------------------

class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(recipient=user).order_by('-timestamp')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
        return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)
# ------------------- Invitations (QR) ----------------------

class InvitationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvitationSerializer

    def get_queryset(self):
        return Invitation.objects.filter(sender=self.request.user, status='pending').order_by('-created_at')

class InvitationUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, id=invitation_id, receiver=request.user, status='pending')
        serializer = InvitationSerializer(invitation)
        return Response(serializer.data)

    def patch(self, request, invitation_id):
        action = request.data.get('action')
        invitation = get_object_or_404(Invitation, id=invitation_id, receiver=request.user)

        if action not in ['accept', 'ignore']:
            return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

        if invitation.status != 'pending':
            return Response({'detail': 'Invitation already responded to.'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'accept':
            invitation.status = 'accepted'
            Friendship.objects.create(user1=invitation.sender, user2=invitation.receiver)
        else:
            invitation.status = 'ignored'

        invitation.save()
        serializer = InvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InvitationCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

# ------------------- Attended Events ----------------------

class AttendedEventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = AttendedEvent.objects.filter(user=request.user).order_by('-attended_at')
        serializer = AttendedEventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        serializer = AttendedEventSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ------------------- Friendship Removal (Unfriend) ----------------------

class FriendDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        user = request.user
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "Friend not found"}, status=404)

        friendship = Friendship.objects.filter(
            (Q(user1=user) & Q(user2=friend)) | (Q(user1=friend) & Q(user2=user))
        ).first()

        if not friendship:
            return Response({"error": "Not friends"}, status=400)

        friendship.delete()
        return Response({"message": "Friend removed"}, status=204)
