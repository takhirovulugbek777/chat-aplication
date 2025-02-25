from django.urls import path

from . import views

urlpatterns = [
    path('', views.ChatListAPIView.as_view(), name="chat-list"),
    path('send-message/', views.SendMessageView.as_view(), name="chat-send-message"),
]
