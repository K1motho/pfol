from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
        profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
        bio = models.CharField(blank=True)

        def __str__(self):
                return self.username
        
class FriendRequest(models.Model):
        sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
        receiver = models.ForeignKey(User, related_name='recieved_requests', on_delete=models.CASCADE)
        status = models.CharField(max_length=20, choices=[('pending', 'pending'), ('accepted', 'accepted'), ('declined','Declined')])
        created_At = models.DateTimeField(auto_now_add=True)

        class Meta :
                unique_together = ('sender', 'receiver')

        def __str__(self):
                return f"FriendRequest from {self.sender} to {self.receiver} - {self.status}"
        
class Friendship(models.Model):
        user1 = models.ForeignKey(User, related_name='friend1', on_delete=models.CASCADE)
        user2 = models.ForeignKey(User, related_name='friend2', on_delete=models.CASCADE)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
                unique_together = ('user1', 'user2')

        def __str__(self):
                return f"Friendship between {self.user1} and {self.user2}"
        
class WishListEvent(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        event_id = models.CharField(max_length=100)
        title = models.CharField(max_length=255)
        date = models.CharField(max_length=255)
        image_url = models.URLField()
        added_at = models.DateField(auto_now_add=True)

        def __str__(self):
                return f"WishlistEvent: {self.title} for user {self.user.username}"
        
class AttendedEvent(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        event_id = models.CharField(max_length=100)
        title = models.CharField(max_length=255)
        date = models.CharField(max_length=100)
        image_url = models.URLField()
        attended_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
                return f"AttendedEvent: {self.title} for user {self.user.username}"
        
class Message(models.Model):
        sender = models.ForeignKey(User,related_name='sent_message', on_delete=models.CASCADE)
        reciever = models.ForeignKey(User, related_name='sent_messae', on_delete=models.CASCADE)
        content = models.TextField()
        timestamp = models.DateTimeField ()
        is_read = models.BooleanField(default=False)

        def __str__(self):
                return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"
        
class Notification(models.model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        type = models.CharField(max_length=50)
        content = models.TextField()
        is_read = models.BooleanField(default=True)
        timestamp = models.DateTimeField(auto_now_add=True)

        def __str__(self):
                return f"Notification for {self.user}: {self.type}"