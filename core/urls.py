from django.urls import path
from .views import (
    RegisterView,
    GoogleAuthView,
    ForgotPasswordView,
    ResetPasswordView,
    DiscoverEventsAPIView,
    CheckUsernameView,
    CheckEmailView,
    UserProfileView,
    FriendListAPIView,
    FriendEventsAPIView,
    FriendProfileAPIView,
    SendFriendRequestView,
    UserSearchView,
    MessageListCreateAPIView,
    NotificationsView,
    InvitationListView,
    InvitationCreateView,
    InvitationUpdateView,
    AttendedEventCreateView,
    FriendDeleteAPIView,
    LoginView,MarkAllNotificationsReadView,
    AcceptFriendRequestView,
    RejectFriendRequestView,
)

urlpatterns = [
    # Auth & Registration
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password'),
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    path('check-email/', CheckEmailView.as_view(), name='check-email'),

    # Events
    path('discover/', DiscoverEventsAPIView.as_view(), name='discover-events'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Friends
    path('friends/', FriendListAPIView.as_view(), name='friend-list'),
    path('friend-events/', FriendEventsAPIView.as_view(), name='friend-events'),
    path('friends/<int:friend_id>/', FriendProfileAPIView.as_view(), name='friend-profile'),
    path('friend-requests/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-requests/<int:receiver_id>/', SendFriendRequestView.as_view(), name='cancel_friend_request'),
     path('friend-requests/accept/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
     path('friend-requests/reject/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('friends/delete/<int:friend_id>/', FriendDeleteAPIView.as_view(), name='friend-delete'),

    # User Search
    path('users/search/', UserSearchView.as_view(), name='user-search'),

    # Messages
    path('messages/<int:friend_id>/', MessageListCreateAPIView.as_view(), name='messages'),

    # Notifications
    path('notifications/', NotificationsView.as_view(), name='notifications'),
    path('notifications/mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-read'),

    # Invitations (QR-based)
    path('invitations/', InvitationListView.as_view(), name='invitation-list'),
    path('invitations/create/', InvitationCreateView.as_view(), name='invitation-create'),
    path('invitations/<int:invitation_id>/', InvitationUpdateView.as_view(), name='invitation-detail'),

    # Attended Events
    path('attended-events/', AttendedEventCreateView.as_view(), name='attended-events'),
]
