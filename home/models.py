from django.db import models
from dashboard.models import * 
from django.contrib.auth.models import User



class Request(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requests')
    status = models.CharField(max_length=20,default="waiting")
    created_at = models.DateTimeField(auto_now_add=True)


 
    def __str__(self):
        return f"{self.user.first_name} - {self.event.title}"   

class Rating(models.Model):
    request = models.OneToOneField(Request,on_delete=models.CASCADE,related_name="request_rating")
    event = models.ForeignKey(Event,on_delete=models.CASCADE,related_name="event_ratings")
    stars = models.IntegerField()
    comment = models.TextField(max_length=150)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.request.user.first_name} - {self.request.event.title} Rating"   