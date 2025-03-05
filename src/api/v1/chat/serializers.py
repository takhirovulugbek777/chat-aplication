from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.db import models
from chat.models import Chat, Message, ChatUser, GroupChat
from user_app.models import Profile

User = get_user_model()


class CreateMessageSerializer(serializers.ModelSerializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    chat_id = serializers.CharField(required=False)
    text = serializers.CharField()

    class Meta:
        model = Message
        fields = ('sender', 'receiver', 'chat_id', 'text')

    def validate(self, attrs):
        if 'receiver' not in attrs and 'chat_id' not in attrs:
            raise serializers.ValidationError('Either receiver or chat_id must be provided')
        if 'receiver' in attrs and 'chat_id' in attrs:
            raise serializers.ValidationError('Provide either receiver or chat_id, not both')
        return attrs

    def create(self, validated_data):
        sender = validated_data['sender']
        if 'receiver' in validated_data:
            receiver = validated_data['receiver']
            if sender == receiver:
                raise serializers.ValidationError('Cannot send to yourself')
            chat = Chat.get_or_create(sender, receiver)
        else:
            chat_id = validated_data['chat_id']
            try:
                chat = Chat.objects.get(chat_id=chat_id)
                if not ChatUser.objects.filter(chat=chat, user=sender).exists():
                    raise serializers.ValidationError('You are not a member of this chat')
            except Chat.DoesNotExist:
                raise serializers.ValidationError('Chat not found')

        message = Message.objects.create(sender=sender, chat=chat, text=validated_data['text'])
        ChatUser.objects.filter(chat=chat).exclude(user=sender).update(
            unread_message_count=models.F('unread_message_count') + 1)
        chat.last_message = message
        chat.save()
        return message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    sent_at = serializers.DateTimeField(source='created', format="%Y-%m-%d %H:%M:%S", read_only=True)
    username = serializers.CharField(source='sender.username', read_only=True)
    user_id = serializers.CharField(source='sender.id', read_only=True)

    class Meta:
        model = Message
        fields = ('user_id', 'id', 'text', 'sender_name', 'sent_at', 'username')


class UserSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'image')

    def get_image(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.image.url
        return None


class ChatUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    is_admin = serializers.BooleanField()

    class Meta:
        model = ChatUser
        fields = ('user', 'is_admin', 'joined_at')


class ChatSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='chat_id')
    unread_message_count = serializers.SerializerMethodField()
    last_message = MessageSerializer(allow_null=True)
    name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    is_group = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'id', 'last_message', 'unread_message_count', 'name', 'username', 'image', 'members_count', 'is_group')

    def get_is_group(self, obj):
        return hasattr(obj, 'group')

    def get_unread_message_count(self, obj):
        user = self.context['request'].user
        chat_user = ChatUser.objects.filter(chat=obj, user=user).first()
        return chat_user.unread_message_count if chat_user else 0

    def get_name(self, obj):
        if hasattr(obj, 'group'):
            return obj.group.name
        other_user = obj.users.exclude(user=self.context['request'].user).first()
        return other_user.user.first_name if other_user else "Unknown"

    def get_username(self, obj):
        if hasattr(obj, 'group'):
            return None
        other_user = obj.users.exclude(user=self.context['request'].user).first()
        return other_user.user.username if other_user else "Unknown"

    def get_image(self, obj):
        if hasattr(obj, 'group'):
            return None  # Could return a default group image
        other_user = obj.users.exclude(user=self.context['request'].user).first()
        return other_user.user.profile.image.url if other_user and hasattr(other_user.user, 'profile') else None

    def get_members_count(self, obj):
        return obj.users.count()


class GroupChatDetailSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator = UserSerializer(read_only=True)
    chat_id = serializers.CharField(source='chat.chat_id')

    class Meta:
        model = GroupChat
        fields = ('chat_id', 'name', 'creator', 'members')

    def get_members(self, obj):
        chat_users = ChatUser.objects.filter(chat=obj.chat)
        return ChatUserSerializer(chat_users, many=True).data


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user')

    def validate(self, attrs):
        chat = self.context['chat']
        user = attrs['user']
        if ChatUser.objects.filter(chat=chat, user=user).exists():
            raise serializers.ValidationError("User is already a member of this chat")
        return attrs


class GroupChatCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def validate_name(self, value):
        # Guruh nomi tekshiruvi
        if GroupChat.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(f"This name is already taken by a user or another group.")

        # Foydalanuvchi nomi tekshiruvi
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(f"This name is already taken by a user or another group.")

        return value

    def validate_members(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("There must be at least 2 members in the group.")
        return value

    def create(self, validated_data):
        creator = self.context['request'].user
        chat = Chat.objects.create(chat_id=f"{validated_data['name'].lower()}")
        group_chat = GroupChat.objects.create(
            chat=chat,
            name=validated_data['name'],
            creator=creator
        )

        ChatUser.objects.create(chat=chat, user=creator, is_admin=True)

        for member in validated_data['members']:
            if member != creator:
                ChatUser.objects.create(chat=chat, user=member)

        return group_chat
