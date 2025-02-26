from django.urls import path, include

urlpatterns = [
    path('chats/', include('api.v1.chat.urls')),
    path('user/', include('api.v1.user_app.urls')),
]
