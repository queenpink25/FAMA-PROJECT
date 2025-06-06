from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

class CustomUserManager(BaseUserManager):
    """Manager for CustomUser model"""
    def create_user(self, username, phone_number, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        phone_number = self.normalize_phone_number(phone_number)

        user = self.model(username=username, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def normalize_phone_number(self, phone):
        try:
            parsed = phonenumbers.parse(phone, "UG")  # UG = Uganda
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number for Uganda")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            raise ValueError("Invalid phone number format")

    def create_superuser(self, username, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser):
    """Simplified custom user model for FAMA system"""
    USER_TYPE_CHOICES = [
        ('pilot', 'Pilot'),
        ('cabin_crew', 'Cabin Crew'),
        ('operator', 'Airline Operator'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)  # Full name of the user
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)  # Optional email field
    phone_number = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_active_duty = models.BooleanField(default=False)
    duty_start_time = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)  # For admin access
    is_superuser = models.BooleanField(default=False)  # For superuser access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number','email','full_name']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class CrewProfile(models.Model):
    """Crew member profile with preferences and qualifications"""
    POSITION_CHOICES = [
        ('captain', 'Captain'),
        ('first_officer', 'First Officer'),
        ('senior_cabin_crew', 'Senior Cabin Crew'),
        ('cabin_crew', 'Cabin Crew'),
        ('ground_crew', 'Ground Crew'),
    ]
    
    HAUL_CHOICES = [
        ('short', 'Short Haul'),
        ('long', 'Long Haul'),
        ('both', 'Both'),
    ]
    
    TRAINING_LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('instructor', 'Instructor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    position = models.CharField(max_length=30, choices=POSITION_CHOICES)
    seniority = models.IntegerField(validators=[MinValueValidator(0)])
    training_level = models.CharField(max_length=20, choices=TRAINING_LEVEL_CHOICES)
    languages_spoken = models.JSONField(default=list)  # ['English', 'French', 'Swahili']
    preferred_haul = models.CharField(max_length=10, choices=HAUL_CHOICES)
    active_duty_days = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    standby_duty_days = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(2)])
    reserve_duty_days = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(2)])
    days_off = models.IntegerField(default=2, validators=[MinValueValidator(2), MaxValueValidator(4)])
    standby_start_time = models.TimeField(default='08:00:00')
    standby_end_time = models.TimeField(default='20:00:00')
    reserve_start_time = models.TimeField(default='08:00:00')
    reserve_end_time = models.TimeField(default='20:00:00')
    allow_swapping = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Flight(models.Model):
    """Flight information model"""
    FLIGHT_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flight_number = models.CharField(max_length=10, unique=True)
    departure_airport = models.CharField(max_length=3)  # IATA code
    arrival_airport = models.CharField(max_length=3)    # IATA code
    scheduled_departure = models.DateTimeField()
    scheduled_arrival = models.DateTimeField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    gate = models.CharField(max_length=10, null=True, blank=True)
    aircraft_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=FLIGHT_STATUS_CHOICES, default='scheduled')
    haul_type = models.CharField(max_length=10, choices=CrewProfile.HAUL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DutyRoster(models.Model):
    """Duty roster assignments for crew members"""
    DUTY_TYPE_CHOICES = [
        ('active', 'Active Duty'),
        ('standby', 'Standby'),
        ('reserve', 'Reserve'),
        ('off', 'Off Duty'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crew_member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='duty_assignments')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, null=True, blank=True, related_name='crew_assignments')
    duty_date = models.DateField()
    duty_type = models.CharField(max_length=20, choices=DUTY_TYPE_CHOICES)
    duty_start_time = models.DateTimeField()
    duty_end_time = models.DateTimeField()
    position = models.CharField(max_length=30, choices=CrewProfile.POSITION_CHOICES)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_rosters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['crew_member', 'duty_date']

class FatigueLog(models.Model):
    """Track crew fatigue levels and duty hours"""
    FATIGUE_LEVEL_CHOICES = [
        ('green', 'Legal to Fly'),
        ('orange', 'Warning'),
        ('red', 'Needs Rest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crew_member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='fatigue_logs')
    duty_start = models.DateTimeField()
    duty_end = models.DateTimeField(null=True, blank=True)
    total_duty_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    flight_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    fatigue_level = models.CharField(max_length=10, choices=FATIGUE_LEVEL_CHOICES, default='green')
    rest_required_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FlightSwapRequest(models.Model):
    """Handle flight swap requests between crew members"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requesting_crew = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='swap_requests_made')
    target_crew = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='swap_requests_received')
    requesting_flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='swap_requests_from')
    target_flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='swap_requests_to')
    reason = models.TextField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_swaps')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Alert(models.Model):
    """System alerts and notifications"""
    ALERT_TYPE_CHOICES = [
        ('weather', 'Weather Change'),
        ('gate', 'Gate Change'),
        ('departure', 'Departure Time Change'),
        ('duration', 'Flight Duration Change'),
        ('cancellation', 'Flight Cancellation'),
        ('crew', 'Crew Change'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='alerts')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(CustomUser, through='AlertRecipient', related_name='received_alerts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AlertRecipient(models.Model):
    """Track alert delivery status"""
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    sms_delivery_status = models.CharField(max_length=20, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)