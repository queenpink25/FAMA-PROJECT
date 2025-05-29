from django.db import models
from users.models import User

class FlightAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flight_number = models.CharField(max_length=10)
    departure_time = models.DateTimeField()
    destination = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), 
        ('standby', 'Standby'), 
        ('reserve', 'Reserve'),
        ('off', 'Off')
    ])

class CalendarEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), 
        ('standby', 'Standby'), 
        ('reserve', 'Reserve'), 
        ('off', 'Off')
    ])