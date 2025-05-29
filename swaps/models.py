from django.db import models
from users.models import User
from schedules.models import FlightAssignment

class SwapRequest(models.Model):
    requester = models.ForeignKey(User, related_name='swap_requests', on_delete=models.CASCADE)
    target_user = models.ForeignKey(User, related_name='incoming_swaps', on_delete=models.CASCADE)
    flight = models.ForeignKey(FlightAssignment, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), 
        ('approved', 'Approved'), 
        ('rejected', 'Rejected')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)