from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
@login_required
def chat_view(request):
    return render(request, 'chat/chat.html')


@login_required
def chat_test(request):
    return render(request, 'chat/test-chat.html')