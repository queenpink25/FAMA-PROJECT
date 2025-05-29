from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('cabin_crew', 'Cabin Crew'),
        ('pilot', 'Pilot'),
        ('operator', 'Operator'),
        ('occ', 'OCC'),  # Operations Control Center
        ('admin', 'System Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
