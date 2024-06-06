from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from pymongo import MongoClient
from django.conf import settings
from bson.objectid import ObjectId
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from .utils import MongoUser

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]
users_collection = db['users']

class MongoDBAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            payload = AccessToken(token).payload
            user_id = payload.get('user_id')
            if not ObjectId.is_valid(user_id):
                raise AuthenticationFailed('Invalid user ID')
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                raise AuthenticationFailed('User not found')
            return (MongoUser(user), token)
        except Exception as e:
            raise AuthenticationFailed(f'Authentication error: {str(e)}')
