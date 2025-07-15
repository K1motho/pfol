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
        user1 = models.ForeignKey(User, related_name='friend1')
        