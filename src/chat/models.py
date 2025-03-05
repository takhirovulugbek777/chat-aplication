from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError

User = get_user_model()


class UniqueNameField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower()


class Chat(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='last_message_chat')

    @classmethod
    def get_or_create(cls, user1, user2):
        users = sorted([user1.id, user2.id])
        chat_id = f"chat_{users[0]}_{users[1]}"

        chat, created = cls.objects.get_or_create(
            chat_id=chat_id,
            defaults={'chat_id': chat_id}
        )

        if created:
            ChatUser.objects.create(chat=chat, user=user1)
            ChatUser.objects.create(chat=chat, user=user2)

        return chat


class GroupChat(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, related_name='group')
    name = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_chats')

    def __str__(self):
        return self.name


class ChatUser(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    unread_message_count = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('chat', 'user')


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created']
