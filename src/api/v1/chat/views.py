from django.contrib.auth import get_user_model
from django.db.migrations import serializer
from rest_framework import status
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.models import Chat, Message, ChatUser
from user_app.models import Profile
from .serializers import CreateMessageSerializer, ChatSerializer, MessageSerializer
from api.v1.user_app.serializers import UserProfileSerializer, ProfileSerializer

User = get_user_model()


class SendMessageView(GenericAPIView):
    serializer_class = CreateMessageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Message sent successfully",
                "data": {
                    "message_id": message.id,
                    "chat_id": message.chat.chat_id,
                    "text": message.text,
                    "created_at": message.created.strftime("%Y-%m-%d %H:%M:%S"),
                    "sender": {
                        "id": message.sender.id,
                        "username": message.sender.username,
                        "first_name": message.sender.first_name
                    }
                }
            },
            status=status.HTTP_201_CREATED
        )


class ChatListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(users__user=self.request.user)


class ChatHistoryListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    @transaction.atomic
    def get_queryset(self):
        user1 = User.objects.get(id=self.kwargs['chat_id'])
        user2 = self.request.user
        chat = Chat.get_or_create(user1, user2)

        # Update unread messages
        Message.objects.filter(chat=chat, is_read=False).exclude(sender=self.request.user).update(is_read=True)

        # Update unread message count for the user
        ChatUser.objects.filter(chat=chat, user=self.request.user).update(unread_message_count=0)

        # Return the queryset
        return Message.objects.filter(chat=chat)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'status': 'success',
                'message': 'Chat history fetched successfully',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class SearchProfileView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = "username"

    def get_object(self):
        try:
            user = super().get_object()
            return user.profile
        except User.profile.RelatedObjectDoesNotExist:
            raise NotFound({"detail": "Profile not found for this user."})
