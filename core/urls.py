from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from .views import FriendRequestViewSet, WishlistEventViewSet, AttendedEventViewSet, ChatMessageViewSet, RegisterView, UserProfileView, FriendsListView, NotificationListView, NotificationMarkReadView, DiscoverEventsAPIView, GoogleAuthView

router = DefaultRouter()
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-requests')
router.register(r'wishlist-events', WishlistEventViewSet, basename='wishlist-events')
router.register(r'attended-events', AttendedEventViewSet, basename='attended-events')
router.register(r'messages', ChatMessageViewSet, basename='chat-messages')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('friends/', FriendsListView.as_view(), name='friend-list'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
     path('api/events/discover/', DiscoverEventsAPIView.as_view(), name='discover-events'),
      path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('', include(router.urls)),
]
