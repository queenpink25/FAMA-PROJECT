from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, CrewProfile, Flight, DutyRoster, FatigueLog, FlightSwapRequest, Alert, AlertRecipient

# Custom forms for CustomUser
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'phone_number', 'user_type')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'phone_number', 'user_type', 'is_active_duty', 'duty_start_time', 'is_staff', 'is_superuser')

# CustomUser admin configuration
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'phone_number', 'user_type', 'is_active_duty', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('user_type', 'is_active_duty', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('phone_number', 'user_type', 'is_active_duty', 'duty_start_time')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone_number', 'user_type', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('username', 'phone_number')
    ordering = ('username',)
    filter_horizontal = ()  # Explicitly set to empty to avoid default groups/user_permissions

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CrewProfile)
admin.site.register(Flight)
admin.site.register(DutyRoster)
admin.site.register(FatigueLog)
admin.site.register(FlightSwapRequest)
admin.site.register(Alert)
admin.site.register(AlertRecipient)