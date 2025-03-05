from django.contrib.auth import get_user_model
from rest_framework import status
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView, CreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Exists, OuterRef
from user_app.models import Profile
from chat.models import Chat, Message, ChatUser, GroupChat
from api.v1.user_app.serializers import ProfileSerializer
from .serializers import (
    CreateMessageSerializer,
    ChatSerializer,
    MessageSerializer,
    GroupChatCreateSerializer,
    GroupChatDetailSerializer,
    AddMemberSerializer,
    ChatUserSerializer,
)

User = get_user_model()


class SendMessageView(GenericAPIView):
    serializer_class = CreateMessageSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Message sent successfully",
                "data": MessageSerializer(message).data
            },
            status=status.HTTP_201_CREATED
        )


class SearchProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, username):
        try:
            user = User.objects.get(username__iexact=username)
            serializer = ProfileSerializer(Profile.objects.get(user=user))
            return Response(
                {
                    "status": "success",
                    "message": "Profile retrieved successfully",
                    "data": serializer.data,
                    "type": "user"
                },
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            try:
                group_chat = GroupChat.objects.get(chat__chat_id=username)
                serializer = GroupChatDetailSerializer(group_chat)
                return Response(
                    {
                        "status": "success",
                        "message": "Group chat retrieved successfully",
                        "data": serializer.data,
                        "type": "group"
                    },
                    status=status.HTTP_200_OK
                )
            except GroupChat.DoesNotExist:
                return Response(
                    {
                        "status": "error",
                        "message": "No user or group chat found with this username/ID",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND
                )


class ChatListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(
            users__user=user
        ).annotate(
            is_group=Exists(GroupChat.objects.filter(chat=OuterRef('pk')))
        ).exclude(last_message=None).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        personal_chats = [chat for chat in serializer.data if not chat['is_group']]
        group_chats = [chat for chat in serializer.data if chat['is_group']]

        return Response(
            {
                "status": "success",
                "message": "Chats retrieved successfully",
                "data": {
                    "personal_chats": personal_chats,
                    "group_chats": group_chats
                }
            },
            status=status.HTTP_200_OK
        )


class ChatHistoryListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def get_chat(self):
        chat_id = self.kwargs['chat_id']
        try:
            chat = Chat.objects.get(chat_id=chat_id)
            if not ChatUser.objects.filter(chat=chat, user=self.request.user).exists():
                raise PermissionDenied("You are not a member of this chat")
            return chat
        except Chat.DoesNotExist:
            try:
                user1 = User.objects.get(id=chat_id)
                user2 = self.request.user
                return Chat.get_or_create(user1, user2)
            except User.DoesNotExist:
                raise NotFound("Chat not found")

    @transaction.atomic
    def get_queryset(self):
        chat = self.get_chat()
        Message.objects.filter(chat=chat, is_read=False).exclude(sender=self.request.user).update(is_read=True)
        ChatUser.objects.filter(chat=chat, user=self.request.user).update(unread_message_count=0)
        return Message.objects.filter(chat=chat)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'status': 'success',
                'message': 'Chat history retrieved successfully',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class CreateGroupChatView(APIView):
    def post(self, request):
        serializer = GroupChatCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            group_chat = serializer.save()
            return Response({
                "status": "success",
                "message": "Group created successfully",
                "data": {
                    "id": group_chat.id,
                    "name": group_chat.name,
                    "chat_id": group_chat.chat.chat_id
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "This name is already taken by a user or another group.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GroupChatDetailView(RetrieveAPIView):
    serializer_class = GroupChatDetailSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'chat_id'

    def get_object(self):
        chat_id = self.kwargs.get('chat_id')
        try:
            chat = Chat.objects.get(chat_id=chat_id)
            if not ChatUser.objects.filter(chat=chat, user=self.request.user).exists():
                raise PermissionDenied("You are not a member of this chat")
            try:
                return GroupChat.objects.get(chat=chat)
            except GroupChat.DoesNotExist:
                raise NotFound("Group chat not found")
        except Chat.DoesNotExist:
            raise NotFound("Chat not found")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "status": "success",
                "message": "Group chat details retrieved successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class AddGroupMemberView(GenericAPIView):
    serializer_class = AddMemberSerializer
    permission_classes = (IsAuthenticated,)

    def get_chat(self, chat_id):
        try:
            group_chat = GroupChat.objects.get(chat__chat_id=chat_id)
            if not ChatUser.objects.filter(chat=group_chat.chat, user=self.request.user, is_admin=True).exists():
                raise PermissionDenied("You don't have permission to add members to this chat")
            return group_chat
        except GroupChat.DoesNotExist:
            raise NotFound("Group chat not found")

    def post(self, request, chat_id):
        group_chat = self.get_chat(chat_id)
        serializer = self.get_serializer(data=request.data, context={'chat': group_chat.chat})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        ChatUser.objects.create(chat=group_chat.chat, user=user)

        return Response(
            {
                "status": "success",
                "message": "Member added successfully",
                "data": ChatUserSerializer(ChatUser.objects.get(chat=group_chat.chat, user=user)).data
            },
            status=status.HTTP_200_OK
        )


class RemoveGroupMemberView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_group_chat(self, chat_id):
        try:
            chat = Chat.objects.get(chat_id=chat_id)
            group_chat = GroupChat.objects.get(chat=chat)
            if not ChatUser.objects.filter(chat=chat, user=self.request.user, is_admin=True).exists():
                raise PermissionDenied("You don't have permission to remove members from this chat")
            return group_chat
        except (Chat.DoesNotExist, GroupChat.DoesNotExist):
            raise NotFound("Group chat not found")

    def delete(self, request, chat_id, user_id):
        group_chat = self.get_group_chat(chat_id)
        chat = group_chat.chat

        user_to_remove = get_object_or_404(User, id=user_id)

        chat_user = ChatUser.objects.filter(chat=chat, user=user_to_remove).first()
        if not chat_user:
            raise NotFound("User is not a member of this chat")

        if user_to_remove == group_chat.creator and ChatUser.objects.filter(chat=chat, is_admin=True).count() <= 1:
            raise PermissionDenied("Cannot remove the only admin from the chat")

        chat_user.delete()

        return Response(
            {
                "status": "success",
                "message": "Member removed successfully",
                "data": None
            },
            status=status.HTTP_200_OK
        )


class LeaveGroupChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, chat_id):
        try:
            # Find the chat by chat_id
            chat = Chat.objects.get(chat_id=chat_id)

            # Check if it's a group chat by looking for an associated GroupChat instance
            try:
                group_chat = chat.group
            except GroupChat.DoesNotExist:
                raise NotFound("Group chat not found")

        except Chat.DoesNotExist:
            raise NotFound("Group chat not found")

        chat_user = ChatUser.objects.filter(chat=chat, user=request.user).first()
        if not chat_user:
            raise NotFound("You are not a member of this chat")

        # Check if user is the creator and the only admin
        if request.user == group_chat.creator and ChatUser.objects.filter(chat=chat, is_admin=True).count() <= 1:
            other_member = ChatUser.objects.filter(chat=chat).exclude(user=request.user).first()
            if other_member:
                other_member.is_admin = True
                other_member.save()
                group_chat.creator = other_member.user
                group_chat.save()
            else:
                chat.delete()  # This will also delete the group_chat due to CASCADE
                return Response(
                    {
                        "status": "success",
                        "message": "You were the last member. Chat has been deleted.",
                        "data": None
                    },
                    status=status.HTTP_200_OK
                )

        chat_user.delete()

        return Response(
            {
                "status": "success",
                "message": "You have left the chat successfully",
                "data": None
            },
            status=status.HTTP_200_OK
        )
