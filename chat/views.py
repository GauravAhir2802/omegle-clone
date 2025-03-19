from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # Import csrf_exempt
from .models import UserProfile, ChatSession, Message
import json
import requests

# Registration View
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if UserProfile.objects.filter(username=username).exists():
            return render(request, 'chat/register.html', {'error': 'Username already exists'})

        if UserProfile.objects.filter(email=email).exists():
            return render(request, 'chat/register.html', {'error': 'Email already exists'})

        user = UserProfile(username=username, password=password, email=email)
        user.save()
        return redirect('login')
    return render(request, 'chat/register.html')

# Login View
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = UserProfile.objects.get(username=username, password=password)
            request.session['user_id'] = user.id  # Store user ID in session
            return redirect('index')
        except UserProfile.DoesNotExist:
            return render(request, 'chat/login.html', {'error': 'Invalid username or password'})
    return render(request, 'chat/login.html')

# Logout View
def logout(request):
    if 'user_id' in request.session:
        # Call the cleanup_sessions view before logging out
        requests.post(
            'http://127.0.0.1:8000/chat/cleanup_sessions/',
            headers={'X-CSRFToken': request.COOKIES.get('csrftoken')},
            cookies=request.COOKIES
        )
        del request.session['user_id']  # Remove user ID from session
    return redirect('login')

# Chat Index View
def index(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = UserProfile.objects.get(id=request.session['user_id'])
    return render(request, 'chat/index.html', {'user': user})

# Start Chat View
@csrf_exempt
def start_chat(request):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    if request.method == 'GET':
        user = UserProfile.objects.get(id=request.session['user_id'])

        # Find an available session with only one user
        available_sessions = ChatSession.objects.filter(user2__isnull=True).exclude(user1=user)
        if available_sessions.exists():
            # Join an existing session
            chat_session = available_sessions.first()
            chat_session.user2 = user
            chat_session.save()
            connected_user = chat_session.user1.username
            return JsonResponse({
                'status': 'connected',
                'session_id': chat_session.id,
                'connected_user': connected_user
            })
        else:
            # Create a new session and wait for another user to join
            chat_session = ChatSession.objects.create(user1=user)
            return JsonResponse({
                'status': 'waiting',
                'session_id': chat_session.id,
                'connected_user': None
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



# Send Message View
@csrf_exempt
def send_message(request):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            sender = UserProfile.objects.get(id=request.session['user_id'])
            content = data.get('content')
            chat_session = get_object_or_404(ChatSession, id=session_id)
            Message.objects.create(chat_session=chat_session, sender=sender, content=content)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Get Messages View
def get_messages(request):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        chat_session = get_object_or_404(ChatSession, id=session_id)
        messages = Message.objects.filter(chat_session=chat_session).order_by('timestamp')
        messages_data = [{'sender': msg.sender.username, 'content': msg.content, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for msg in messages]
        return JsonResponse({'messages': messages_data})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def cleanup_sessions(request):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    if request.method == 'POST':
        user = UserProfile.objects.get(id=request.session['user_id'])

        # Mark all sessions involving the user as inactive
        ChatSession.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).update(is_active=False)

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def check_connection(request):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        chat_session = get_object_or_404(ChatSession, id=session_id)

        if chat_session.user2:
            # User is connected to another user
            if chat_session.user1.id == request.session['user_id']:
                connected_user = chat_session.user2.username
            else:
                connected_user = chat_session.user1.username
            return JsonResponse({
                'status': 'connected',
                'connected_user': connected_user
            })
        else:
            # User is waiting for another user to join
            return JsonResponse({
                'status': 'waiting',
                'connected_user': None
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)