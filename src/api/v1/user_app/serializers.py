from django.contrib.auth.models import User
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    image = serializers.ImageField(source="profile.image", read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "image", 'bio']


