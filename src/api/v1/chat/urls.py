from django.urls import path

from . import views

urlpatterns = [
    path('', views.ChatListAPIView.as_view(), name="chat-list"),
    path('send-message/', views.SendMessageView.as_view(), name="chat-send-message"),
    path('<str:chat_id>/messages/', views.ChatHistoryListAPIView.as_view(), name='chat-history'),
    path('search/<str:username>/', views.SearchProfileView.as_view(), name='search_profile'),
]
