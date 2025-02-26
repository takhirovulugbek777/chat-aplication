from django.urls import path
from .views import UserDetailAPIView

urlpatterns = [
    path("user/<int:id>/", UserDetailAPIView.as_view(), name="user-detail"),

]
