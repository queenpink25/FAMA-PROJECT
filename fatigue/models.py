from django.db import models
from users.models import User

class DutyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    duty_start = models.DateTimeField()
    duty_end = models.DateTimeField()
    flight_time_hours = models.DecimalField(max_digits=5, decimal_places=2)

    @property
    def fatigue_level(self):
        # Example logic: adjust as needed
        total_hours = (self.duty_end - self.duty_start).total_seconds() / 3600
        if total_hours < 8:
            return 'Green'
        elif total_hours < 12:
            return 'Orange'
        else:
            return 'Red'
