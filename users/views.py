from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from social_network.mongo import users_collection
from django.core.cache import cache
from .utils import MongoUser, get_tokens_for_user 
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    data = request.data
    if users_collection.find_one({"email": data['email']}):
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    hashed_password = make_password(data['password'])

    user_data = {
        "username": data['username'],
        "email": data['email'],
        "password": hashed_password,
        "friends": [],
        "friend_requests": []
    }

    result = users_collection.insert_one(user_data)
    
    user = users_collection.find_one({"_id": result.inserted_id})
    token = get_tokens_for_user(user)
    return Response({
        "user": UserSerializer(user).data,
        "token": token
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    data = request.data
    user = users_collection.find_one({"email": data['email']})
    if not user or not check_password(data['password'], user['password']):
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    tokens = get_tokens_for_user(user)
    
    response = Response({'detail': 'Login successful'})
    response.set_cookie(
        key='access_token',
        value=tokens['access'],
        httponly=True,
        secure=False, 
        samesite='Lax'
    )
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh'],
        httponly=True,
        secure=False,  
        samesite='Lax' 
    )
    response['X-CSRFToken'] = get_token(request)
    return response

@api_view(['POST'])
def logout_view(request):
    response = Response({'detail': 'Logout successful'})
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    from_user = request.user.email  
    to_user_email = request.data['to_user_email']
    if from_user == to_user_email:
        return Response({"error": "Cannot send friend request to yourself"}, status=status.HTTP_400_BAD_REQUEST)
    request_count_key = f"friend_request_count:{from_user}"
    request_count = cache.get(request_count_key, 0)
    if request_count >= 3:
        return Response({"error": "Exceeded the limit of 3 friend requests within a minute"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    to_user = users_collection.find_one({"email": to_user_email})
    if not to_user:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if from_user in to_user['friend_requests']:
        return Response({"error": "Friend request already sent"}, status=status.HTTP_400_BAD_REQUEST)
    
    users_collection.update_one({"email": to_user_email}, {"$push": {"friend_requests": from_user}})
    cache.set(request_count_key, request_count + 1, timeout=60)
    
    return Response({"message": "Friend request sent"}, status=status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([AllowAny])
def search_users(request):
    keyword = request.query_params.get('keyword', '')
    page_number = request.query_params.get('page', 1)
    paginator = PageNumberPagination()
    paginator.page_size = 10

    if "@" in keyword:
        users = users_collection.find({"email": keyword})
    else:
        users = users_collection.find({"username": {"$regex": keyword, "$options": "i"}})

    paginated_users = paginator.paginate_queryset(list(users), request)
    serialized_users = UserSerializer(paginated_users, many=True).data
    return paginator.get_paginated_response(serialized_users)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_friend_request(request):
    from_user_email = request.data['from_user_email']
    action = request.data['action']
    self_email = request.user.email
    
    if action == 'accept':
        users_collection.update_one({"email": self_email}, {"$pull": {"friend_requests": from_user_email}, "$push": {"friends": from_user_email}})
        users_collection.update_one({"email": from_user_email}, {"$push": {"friends": self_email}})
    elif action == 'reject':
        users_collection.update_one({"email": from_user_email}, {"$pull": {"friend_requests": from_user_email}})
    
    return Response({"message": f"Friend request {action}ed"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_friends(request):
    self_email = request.user.email
    user = users_collection.find_one({"email": self_email})
    friends = user['friends']
    return Response({"friends": friends}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pending_requests(request):
    self_email = request.user.email
    user = users_collection.find_one({"email": self_email})
    pending_requests = user['friend_requests']
    return Response({"pending_requests": pending_requests}, status=status.HTTP_200_OK)


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token not found'}, status=400)

        serializer = self.get_serializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)

        response = Response(serializer.validated_data)
        response.set_cookie(
            key='access_token',
            value=serializer.validated_data['access'],
            httponly=True,
            secure=False,  
            samesite='Lax' 
        )
        return response
