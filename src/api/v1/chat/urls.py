from django.urls import path
from .views import (
    SendMessageView,
    ChatListAPIView,
    ChatHistoryListAPIView,
    SearchProfileView,
    CreateGroupChatView,
    GroupChatDetailView,
    AddGroupMemberView,
    RemoveGroupMemberView,
    LeaveGroupChatView,
)

urlpatterns = [
    path('send-message/', SendMessageView.as_view(), name='send_message'),
    path('', ChatListAPIView.as_view(), name='chat_list'),
    path('chat-history/<str:chat_id>/', ChatHistoryListAPIView.as_view(), name='chat_history'),
    path('search-profile/<str:username>/', SearchProfileView.as_view(), name='search_profile'),


    path('create-group/', CreateGroupChatView.as_view(), name='create_group_chat'),
    path('group/<str:chat_id>/', GroupChatDetailView.as_view(), name='group_chat_detail'),
    path('group/<str:chat_id>/add-member/', AddGroupMemberView.as_view(), name='add_group_member'),
    path('group/<str:chat_id>/remove-member/<int:user_id>/', RemoveGroupMemberView.as_view(),
         name='remove_group_member'),
    path('group/<str:chat_id>/leave/', LeaveGroupChatView.as_view(), name='leave_group_chat'),
]
