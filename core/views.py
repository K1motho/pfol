from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import models

from .models import FriendRequest, Friendship, WishListEvent, AttendedEvent, Message, Notification
from .serializers import (
    UserSerializer, RegisterSerializer, FriendRequestSerializer, FriendshipSerializer,
    WishlistEventSerializer, AttendedEventSerializer, MessageSerializer, NotificationSerializer
)

User = get_user_model()

# Registration view
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


# User Profile view (retrieve/update)
class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# Friend Requests viewset
class FriendRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(receiver=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friend_request = get_object_or_404(FriendRequest, pk=pk, receiver=request.user)
        if friend_request.status != 'pending':
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)

        if Friendship.objects.filter(user1=friend_request.sender, user2=friend_request.receiver).exists():
            return Response({'detail': 'Already friends'}, status=status.HTTP_400_BAD_REQUEST)

        friend_request.status = 'accepted'
        friend_request.save()

        # Create friendship both ways
        Friendship.objects.create(user1=friend_request.sender, user2=friend_request.receiver)
        Friendship.objects.create(user1=friend_request.receiver, user2=friend_request.sender)
        return Response({'detail': 'Friend request accepted', 'status': friend_request.status})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        friend_request = get_object_or_404(FriendRequest, pk=pk, receiver=request.user)
        if friend_request.status != 'pending':
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)
        friend_request.status = 'declined'
        friend_request.save()
        return Response({'detail': 'Friend request declined', 'status': friend_request.status})


# Friends List
class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        friendships = Friendship.objects.filter(user1=self.request.user)
        friend_ids = friendships.values_list('user2__id', flat=True)
        return User.objects.filter(id__in=friend_ids)


# Wishlist Event Views
class WishlistEventViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishListEvent.objects.filter(user=self.request.user).order_by('-added_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Attended Event Views
class AttendedEventViewSet(viewsets.ModelViewSet):
    serializer_class = AttendedEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AttendedEvent.objects.filter(user=self.request.user).order_by('-attended_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Chat Messages
class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friend_id = self.request.query_params.get('friend_id')
        try:
            friend_id = int(friend_id)
        except (TypeError, ValueError):
            return Message.objects.none()

        return Message.objects.filter(
            (models.Q(sender=user) & models.Q(receiver_id=friend_id)) |
            (models.Q(sender_id=friend_id) & models.Q(receiver=user))
        ).order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


# Notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-timestamp')


class NotificationMarkReadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'detail': 'Notification marked as read.'}, status=status.HTTP_200_OK)
