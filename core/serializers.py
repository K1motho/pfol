from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendRequest, Friendship, WishListEvent, AttendedEvent, Message, Notification, Event, Invitation
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# -----------------------------
# User & Registration
# -----------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_pic', 'bio']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.profile_pic.url if instance.profile_pic and hasattr(instance.profile_pic, 'url') else None
        return rep

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom fields to response
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data

# -----------------------------
# Friend Requests & Friendships
# -----------------------------
class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']

class FriendshipSerializer(serializers.ModelSerializer):
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'user1', 'user2', 'created_at']

# -----------------------------
# Events (Wishlist & Attended)
# -----------------------------
class WishlistEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishListEvent
        fields = ['id', 'event_id', 'title', 'date', 'image_url', 'added_at']

class AttendedEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendedEvent
        fields = ['id', 'event_id', 'title', 'date', 'image_url', 'attended_at']

# -----------------------------
# Messages & Notifications
# -----------------------------
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'is_read']

class NotificationSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    recipient_id = serializers.IntegerField(source='recipient.id', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'type', 'content', 'is_read', 'timestamp', 'sender_id', 'sender_name', 'recipient_id', 'recipient_name']
# -----------------------------
# Events
# -----------------------------
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'date',
            'location',
            'image',
            'is_public',
            'ticket_price',
            'created_by',
            'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

class FriendEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    date = serializers.CharField()
    image_url = serializers.CharField()

# -----------------------------
# Friend Profile
# -----------------------------
class FriendProfileSerializer(serializers.ModelSerializer):
    mutual_events = AttendedEventSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'mutual_events']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.profile_pic.url if instance.profile_pic and hasattr(instance.profile_pic, 'url') else None
        return rep

# -----------------------------
# Invitation (for QR Code)
# -----------------------------
class InvitationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Invitation
        fields = ['id', 'sender', 'sender_name', 'receiver', 'receiver_name', 'status', 'created_at']
        read_only_fields = ['id', 'sender', 'sender_name', 'receiver_name', 'created_at']
