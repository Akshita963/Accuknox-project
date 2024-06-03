# api/urls.py

from django.urls import path
from .views import signup, login, search_users, send_friend_request, handle_friend_request, list_friends, list_pending_requests

urlpatterns = [
    path('signup/', signup),
    path('login/', login),
    path('search_users/', search_users),
    path('send_friend_request/', send_friend_request),
    path('handle_friend_request/', handle_friend_request),
    path('list_friends/', list_friends),
    path('list_pending_requests/', list_pending_requests),
]
