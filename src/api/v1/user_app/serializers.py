from django.contrib.auth.models import User
from rest_framework import serializers

from user_app.models import Profile


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    image = serializers.ImageField(source="profile.image", read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    username = serializers.CharField(source='profile.username', read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "image", 'bio']


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.CharField(source="user.id", read_only=True)

    class Meta:
        model = Profile
        fields = ["username", 'full_name', "bio", "image", 'user_id']
