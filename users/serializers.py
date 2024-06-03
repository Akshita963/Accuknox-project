# api/serializers.py

from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    friends = serializers.ListField(child=serializers.EmailField(), default=[])
    friend_requests = serializers.ListField(child=serializers.EmailField(), default=[])
