from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendRequest, Friendship, WishListEvent,AttendedEvent, Message, Notification

User = get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_pic', 'bio']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

        def create(self,validated_data):
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            return user

class FriendRequstSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reciever = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']

class FiendshipSerializer(serializers.ModelSerializer):
    user1= UserSerializer(read_only=True)
    user2= UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields= ['id', 'user1', 'user2', 'created_at']

class WishlistEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishListEvent
        fields =['id', 'event_id', 'title', 'date', 'image_url', 'added_at']

class AttenedEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendedEvent
        fields = ['id', 'event_id', 'title', 'date', 'image_url', 'attended_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'is_read']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'content', 'is_read', 'timestamp']