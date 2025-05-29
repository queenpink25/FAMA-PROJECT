from django.db import models
from users.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    seniority = models.PositiveIntegerField(help_text="Years of experience")
    training_level = models.IntegerField()
    languages_spoken = models.CharField(max_length=200)
    preferred_haul = models.CharField(max_length=10, choices=[('short', 'Short'), ('long', 'Long')])
    active_days = models.JSONField()  # e.g., ["Monday", "Tuesday", "Friday"]
    standby_day = models.CharField(max_length=10)
    standby_start = models.TimeField()
    standby_end = models.TimeField()
    reserve_day = models.CharField(max_length=10)
    reserve_start = models.TimeField()
    reserve_end = models.TimeField()
    off_days = models.JSONField()  # e.g., ["Saturday", "Sunday"]