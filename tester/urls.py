from django.urls import path
from .views import EventbriteProxyView

urlpatterns = [
    # ... your other urls
    path('eventbrite-events/', EventbriteProxyView.as_view(), name='eventbrite-proxy'),
]
