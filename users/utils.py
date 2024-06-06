# utils.py

from rest_framework_simplejwt.tokens import RefreshToken
from bson import ObjectId

class MongoUser:
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.email = user_data["email"]
        self.password = user_data["password"]

    def __str__(self):
        return self.email
    @property
    def is_authenticated(self):
        return True

def get_tokens_for_user(user_data):
    user = MongoUser(user_data)
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
