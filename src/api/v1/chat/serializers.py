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
            chat_user, _ = ChatUser.objects.get_or_create(chat=chat, user=validated_data['receiver'])
            message = Message.objects.create(sender=validated_data['sender'], chat=chat, text=validated_data['text'])
            ChatUser.objects.filter(id=chat_user.id).update(unread_count=F('unread_count') + 1)
            chat.last_message = message
            chat.save()
            return message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            'id',
            'text'
        )


class ChatSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    unread_message_count = serializers.SerializerMethodField()
    last_message = MessageSerializer()

    class Meta:
        model = Chat
        fields = (
            'id',
            'last_message',
            'unread_message_count'
        )

    def get_id(self, instance):
        return ChatUser.objects.filter(chat=instance).exclude(user=self.context['request'].user).first().user_id

    def get_unread_message_count(self, instance: Chat):
        return ChatUser.objects.filter(chat=instance, user=self.context['request'].user).first().unread_message_count
