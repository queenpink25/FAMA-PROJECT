from django.db import models
from users.models import User

class Alert(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    alert_type = models.CharField(max_length=50, choices=[
        ('weather', 'Weather'), 
        ('gate_change', 'Gate Change'),
        ('departure_time', 'Departure Time'),
        ('flight_time', 'Flight Time')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
