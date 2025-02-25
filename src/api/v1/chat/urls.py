from django.urls import path

from . import views

urlpatterns = [
    path('send-message/', views.SendMessageView.as_view(), name="chat-send-message"),
    path('history/', views.ChatHistoryView.as_view(), name="chat-history"),
]
