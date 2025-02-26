from django.contrib.auth import get_user_model
from rest_framework import status, serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.models import Chat, Message, ChatUser
from .serializers import CreateMessageSerializer, ChatSerializer, MessageSerializer
User = get_user_model()

class SendMessageView(GenericAPIView):
    serializer_class = CreateMessageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response({'message_id': message.id}, status=status.HTTP_201_CREATED)


class ChatListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(users__user=self.request.user)


class ChatHistoryListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def get_queryset(self):
        user1 = User.objects.get(id=self.kwargs['chat_id'])
        user2=self.request.user
        chat = Chat.get_or_create(user1, user2)
        return Message.objects.filter(chat=chat).order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        unread_messages = queryset.filter(is_read=False).exclude(id=request.user.id)
        unread_messages.update(is_read=True)

        ChatUser.objects.filter(chat_id=self.kwargs['chat_id'], user=request.user).update(unread_message_count=0)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'status': 'success',
                'message': 'Chat history fetched successfully',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
