from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView, ListAPIView
from .serializers import UserProfileSerializer
from django.db.models import Count, Max


class UserDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "id"
