from django.urls import path, include
from .views import (
    DiscoverEventsAPIView,
    GoogleAuthView,
    RegisterView,
    CheckUsernameView,
    CheckEmailView,
    UserProfileView,
    FriendListAPIView,
    FriendEventsAPIView,
    FriendProfileAPIView,
    MessageListCreateAPIView,
    NotificationsView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('events/discover/', DiscoverEventsAPIView.as_view(), name='discover-events'),
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/check-username', CheckUsernameView.as_view(), name='check-username'),
    path('auth/check-email', CheckEmailView.as_view(), name='check-email'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # ✅ New friend-related endpoints:
    path('friends/', FriendListAPIView.as_view(), name='friend-list'),
    path('friend-events/', FriendEventsAPIView.as_view(), name='friend-events'),
    path('friends/<int:friend_id>/', FriendProfileAPIView.as_view(), name='friend-profile'),
     path('api/messages/<int:friend_id>/', MessageListCreateAPIView.as_view(), name='messages'),
     path('notifications/', NotificationsView.as_view(), name='notifications'),
]
