from django.urls import path, include

urlpatterns = [
    path('chats/', include('api.v1.chat.urls'))
]