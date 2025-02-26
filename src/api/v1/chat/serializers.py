from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from chat.models import Message, Chat, ChatUser

User = get_user_model()


class CreateMessageSerializer(serializers.ModelSerializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    text = serializers.CharField()

    class Meta:
        model = Message
        fields = (
            'sender',
            'receiver',
            'text',
        )

    def create(self, validated_data):
        with transaction.atomic():
            if validated_data['sender'] == validated_data['receiver']:
                raise serializers.ValidationError('Can not send to yourself')
            chat = Chat.get_or_create(validated_data['sender'], validated_data['receiver'])
            message = Message.objects.create(sender=validated_data['sender'], chat=chat, text=validated_data['text'])
            ChatUser.objects.filter(
                chat=chat,
                user=validated_data['receiver']
            ).update(unread_message_count=F('unread_message_count') + 1)
            chat.last_message = message
            chat.save()
            return message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    sent_at = serializers.DateTimeField(source='created', format="%Y-%m-%d %H:%M:%S", read_only=True)
    username = serializers.CharField(source='sender.username', read_only=True)
    class Meta:
        model = Message
        fields = (
            'id',
            'text',
            'sender_name',
            'sent_at',
            'username',
        )


class ChatSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    unread_message_count = serializers.SerializerMethodField()
    last_message = MessageSerializer()
    name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'id',
            'last_message',
            'unread_message_count',
            'name',
            'username',
        )

    def get_id(self, instance):
        return ChatUser.objects.filter(chat=instance).exclude(user=self.context['request'].user).first().user_id

    def get_unread_message_count(self, instance: Chat):
        return ChatUser.objects.filter(chat=instance, user=self.context['request'].user).first().unread_message_count

    def get_name(self, instance: Chat):
        return ChatUser.objects.filter(chat=instance).exclude(user=self.context['request'].user).first().user.first_name

    def get_username(self, instance: Chat):
        return ChatUser.objects.filter(chat=instance).exclude(user=self.context['request'].user).first().user.username
