from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # In a real app, use hashed passwords
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

class ChatSession(models.Model):
    user1 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user1_sessions')
    user2 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user2_sessions', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Track session activity

    def __str__(self):
        return f"ChatSession {self.id}"

class Message(models.Model):
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in session {self.chat_session.id}"