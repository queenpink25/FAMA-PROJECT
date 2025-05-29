from django.db import models

class CrewMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)