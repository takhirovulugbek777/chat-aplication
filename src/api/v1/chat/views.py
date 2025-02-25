from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.models import Chat
from .serializers import CreateMessageSerializer, ChatSerializer


class SendMessageView(GenericAPIView):
    serializer_class = CreateMessageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response({'message_id': message.id}, status=status.HTTP_201_CREATED)


class ChatHistoryView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(users__user=self.request.user)
