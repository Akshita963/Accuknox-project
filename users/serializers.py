# serializers.py

from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    friends = serializers.ListField(child=serializers.CharField(), required=False)
    friend_requests = serializers.ListField(child=serializers.CharField(), required=False)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance
