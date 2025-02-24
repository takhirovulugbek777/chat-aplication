from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import CreateMessageSerializer


class SendMessageView(GenericAPIView):
    serializer_class = CreateMessageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response({'message_id': message.id}, status=status.HTTP_201_CREATED)
