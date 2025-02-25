from typing import TYPE_CHECKING

from django.db import models
from model_utils.models import TimeStampedModel

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class Chat(TimeStampedModel):
    chat_id = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField('auth.User')
    last_message = models.ForeignKey('chat.Message', on_delete=models.CASCADE, related_name="+", null=True, blank=True)

    @classmethod
    def get_or_create(cls, sender: "User", receiver: "User"):
        if sender.id > receiver.id:
            _chat_id = f'chat_{sender.id}_{receiver.id}'
        else:
            _chat_id = f'chat_{receiver.id}_{sender.id}'

        chat, created = cls.objects.get_or_create(chat_id=_chat_id)
        if created:
            chat.participants.add(receiver)
            chat.participants.add(sender)
            ChatUser.objects.create(chat=chat, user=receiver)
            ChatUser.objects.create(chat=chat, user=sender)
        return chat


class Message(TimeStampedModel):
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    chat = models.ForeignKey('chat.Chat', on_delete=models.CASCADE)
    text = models.TextField()


class ChatUser(TimeStampedModel):
    chat = models.ForeignKey('chat.Chat', on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    unread_message_count = models.PositiveIntegerField(default=0)
    last_read_at = models.DateTimeField(null=True, blank=True)
