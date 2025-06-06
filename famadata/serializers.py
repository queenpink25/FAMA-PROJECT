from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CustomUser, CrewProfile, Flight, DutyRoster, 
    FatigueLog, FlightSwapRequest, Alert, AlertRecipient
)
from phonenumbers import parse, is_valid_number, format_number, PhoneNumberFormat, NumberParseException


User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'user_type',
            'phone_number', 'is_active_duty', 'duty_start_time',
            'created_at', 'is_staff', 'updated_at', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate_phone_number(self, value):
        try:
            parsed = parse(value, "UG")
            if not is_valid_number(parsed):
                raise serializers.ValidationError("Invalid phone number for Uganda.")
            return format_number(parsed, PhoneNumberFormat.E164)  # +256...
        except NumberParseException:
            raise serializers.ValidationError("Phone number format is not recognized.")

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class CrewProfileSerializer(serializers.ModelSerializer):
    """Serializer for CrewProfile model"""
    user_details = CustomUserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CrewProfile
        fields = [
            'id', 'user', 'user_details', 'position', 'seniority', 'training_level',
            'languages_spoken', 'preferred_haul', 'active_duty_days', 'standby_duty_days',
            'reserve_duty_days', 'days_off', 'standby_start_time', 'standby_end_time',
            'reserve_start_time', 'reserve_end_time', 'allow_swapping',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class FlightSerializer(serializers.ModelSerializer):
    """Serializer for Flight model"""
    duration = serializers.SerializerMethodField()
    crew_assignments = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'departure_airport', 'arrival_airport',
            'scheduled_departure', 'scheduled_arrival', 'actual_departure',
            'actual_arrival', 'gate', 'aircraft_type', 'status', 'haul_type',
            'duration', 'crew_assignments', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def get_duration(self, obj):
        """Calculate flight duration"""
        if obj.scheduled_departure and obj.scheduled_arrival:
            duration = obj.scheduled_arrival - obj.scheduled_departure
            return str(duration)
        return None


class DutyRosterSerializer(serializers.ModelSerializer):
    """Serializer for DutyRoster model"""
    crew_member_details = CustomUserSerializer(source='crew_member', read_only=True)
    flight_details = FlightSerializer(source='flight', read_only=True)
    created_by_details = CustomUserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = DutyRoster
        fields = [
            'id', 'crew_member', 'crew_member_details', 'flight', 'flight_details',
            'duty_date', 'duty_type', 'duty_start_time', 'duty_end_time', 'position',
            'created_by', 'created_by_details', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class FatigueLogSerializer(serializers.ModelSerializer):
    """Serializer for FatigueLog model"""
    crew_member_details = CustomUserSerializer(source='crew_member', read_only=True)
    
    class Meta:
        model = FatigueLog
        fields = [
            'id', 'crew_member', 'crew_member_details', 'duty_start', 'duty_end',
            'total_duty_hours', 'flight_hours', 'fatigue_level', 'rest_required_until',
            'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }


class FlightSwapRequestSerializer(serializers.ModelSerializer):
    """Serializer for FlightSwapRequest model"""
    requesting_crew_details = CustomUserSerializer(source='requesting_crew', read_only=True)
    target_crew_details = CustomUserSerializer(source='target_crew', read_only=True)
    requesting_flight_details = FlightSerializer(source='requesting_flight', read_only=True)
    target_flight_details = FlightSerializer(source='target_flight', read_only=True)
    approved_by_details = CustomUserSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = FlightSwapRequest
        fields = [
            'id', 'requesting_crew', 'requesting_crew_details', 'target_crew',
            'target_crew_details', 'requesting_flight', 'requesting_flight_details',
            'target_flight', 'target_flight_details', 'reason', 'status',
            'approved_by', 'approved_by_details', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class AlertRecipientSerializer(serializers.ModelSerializer):
    """Serializer for AlertRecipient model"""
    recipient_details = CustomUserSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = AlertRecipient
        fields = [
            'alert', 'recipient', 'recipient_details', 'is_read', 'sms_sent',
            'sms_delivery_status', 'read_at', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    flight_details = FlightSerializer(source='flight', read_only=True)
    created_by_details = CustomUserSerializer(source='created_by', read_only=True)
    recipients_details = AlertRecipientSerializer(source='alertrecipient_set', many=True, read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'message', 'flight',
            'flight_details', 'created_by', 'created_by_details', 'recipients',
            'recipients_details', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }


# Simplified serializers for dropdown/choice endpoints
class UserChoiceSerializer(serializers.ModelSerializer):
    """Simplified user serializer for dropdown choices"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name', 'user_type']
    
    def get_display_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name and obj.last_name else obj.username


class FlightChoiceSerializer(serializers.ModelSerializer):
    """Simplified flight serializer for dropdown choices"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Flight
        fields = ['id', 'flight_number', 'departure_airport', 'arrival_airport', 'display_name', 'scheduled_departure']
    
    def get_display_name(self, obj):
        return f"{obj.flight_number} ({obj.departure_airport} → {obj.arrival_airport})"