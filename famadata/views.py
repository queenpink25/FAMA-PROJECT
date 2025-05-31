from rest_framework import generics, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    CustomUser, CrewProfile, Flight, DutyRoster, 
    FatigueLog, FlightSwapRequest, Alert, AlertRecipient
)
from .serializers import (
    CustomUserSerializer, CrewProfileSerializer, FlightSerializer,
    DutyRosterSerializer, FatigueLogSerializer, FlightSwapRequestSerializer,
    AlertSerializer, AlertRecipientSerializer, UserChoiceSerializer,
    FlightChoiceSerializer
)


class CustomUserViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomUser model"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_active_duty']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['username', 'created_at', 'last_login']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get simplified user data for dropdown choices"""
        users = self.get_queryset()
        serializer = UserChoiceSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_crew(self, request):
        """Get currently active crew members"""
        active_crew = self.get_queryset().filter(
            is_active_duty=True,
            user_type__in=['pilot', 'cabin_crew']
        )
        serializer = self.get_serializer(active_crew, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_duty_status(self, request, pk=None):
        """Toggle user's active duty status"""
        user = self.get_object()
        user.is_active_duty = not user.is_active_duty
        if user.is_active_duty:
            user.duty_start_time = timezone.now()
        else:
            user.duty_start_time = None
        user.save()
        return Response({
            'status': 'success',
            'is_active_duty': user.is_active_duty,
            'duty_start_time': user.duty_start_time
        })
    
    def get_permissions(self):
        # Allow anyone to create (register), require auth for all other actions
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()


class CrewProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for CrewProfile model"""
    queryset = CrewProfile.objects.select_related('user').all()
    serializer_class = CrewProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['position', 'training_level', 'preferred_haul', 'allow_swapping']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'position']
    ordering_fields = ['seniority', 'created_at']
    ordering = ['-seniority']
    
    @action(detail=False, methods=['get'])
    def by_position(self, request):
        """Get crew profiles grouped by position"""
        positions = {}
        for choice in CrewProfile.POSITION_CHOICES:
            position_code, position_name = choice
            profiles = self.get_queryset().filter(position=position_code)
            serializer = self.get_serializer(profiles, many=True)
            positions[position_name] = serializer.data
        return Response(positions)


class FlightViewSet(viewsets.ModelViewSet):
    """ViewSet for Flight model"""
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'haul_type', 'departure_airport', 'arrival_airport']
    search_fields = ['flight_number', 'departure_airport', 'arrival_airport']
    ordering_fields = ['scheduled_departure', 'scheduled_arrival', 'created_at']
    ordering = ['scheduled_departure']
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get simplified flight data for dropdown choices"""
        flights = self.get_queryset()
        serializer = FlightChoiceSerializer(flights, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's flights"""
        today = timezone.now().date()
        flights = self.get_queryset().filter(
            scheduled_departure__date=today
        )
        serializer = self.get_serializer(flights, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get flights grouped by status"""
        statuses = {}
        for choice in Flight.FLIGHT_STATUS_CHOICES:
            status_code, status_name = choice
            flights = self.get_queryset().filter(status=status_code)
            serializer = self.get_serializer(flights, many=True)
            statuses[status_name] = serializer.data
        return Response(statuses)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update flight status"""
        flight = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in [choice[0] for choice in Flight.FLIGHT_STATUS_CHOICES]:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        flight.status = new_status
        if new_status == 'completed' and not flight.actual_arrival:
            flight.actual_arrival = timezone.now()
        flight.save()
        
        serializer = self.get_serializer(flight)
        return Response(serializer.data)


class DutyRosterViewSet(viewsets.ModelViewSet):
    """ViewSet for DutyRoster model"""
    queryset = DutyRoster.objects.select_related(
        'crew_member', 'flight', 'created_by'
    ).all()
    serializer_class = DutyRosterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['duty_type', 'position', 'duty_date', 'crew_member']
    search_fields = ['crew_member__username', 'flight__flight_number']
    ordering_fields = ['duty_date', 'duty_start_time', 'created_at']
    ordering = ['duty_date', 'duty_start_time']
    
    @action(detail=False, methods=['get'])
    def by_crew_member(self, request):
        """Get duty roster for a specific crew member"""
        crew_member_id = request.query_params.get('crew_member_id')
        if not crew_member_id:
            return Response(
                {'error': 'crew_member_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rosters = self.get_queryset().filter(crew_member_id=crew_member_id)
        serializer = self.get_serializer(rosters, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly_schedule(self, request):
        """Get weekly schedule for crew members"""
        start_date = request.query_params.get('start_date')
        if not start_date:
            start_date = timezone.now().date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = start_date + timedelta(days=6)
        
        rosters = self.get_queryset().filter(
            duty_date__gte=start_date,
            duty_date__lte=end_date
        )
        serializer = self.get_serializer(rosters, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Check for scheduling conflicts"""
        conflicts = []
        rosters = self.get_queryset().select_related('crew_member')
        
        # Group by crew member and date
        crew_schedules = {}
        for roster in rosters:
            key = (roster.crew_member.id, roster.duty_date)
            if key not in crew_schedules:
                crew_schedules[key] = []
            crew_schedules[key].append(roster)
        
        # Check for overlapping duties
        for schedules in crew_schedules.values():
            if len(schedules) > 1:
                for i, schedule1 in enumerate(schedules):
                    for schedule2 in schedules[i+1:]:
                        if (schedule1.duty_start_time < schedule2.duty_end_time and
                            schedule2.duty_start_time < schedule1.duty_end_time):
                            conflicts.append({
                                'crew_member': schedule1.crew_member.username,
                                'date': schedule1.duty_date,
                                'conflict_duties': [
                                    self.get_serializer(schedule1).data,
                                    self.get_serializer(schedule2).data
                                ]
                            })
        
        return Response(conflicts)


class FatigueLogViewSet(viewsets.ModelViewSet):
    """ViewSet for FatigueLog model"""
    queryset = FatigueLog.objects.select_related('crew_member').all()
    serializer_class = FatigueLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['fatigue_level', 'crew_member']
    search_fields = ['crew_member__username']
    ordering_fields = ['duty_start', 'total_duty_hours', 'created_at']
    ordering = ['-duty_start']
    
    @action(detail=False, methods=['get'])
    def fatigue_alerts(self, request):
        """Get crew members with high fatigue levels"""
        high_fatigue = self.get_queryset().filter(
            fatigue_level__in=['orange', 'red']
        ).order_by('-duty_start')
        serializer = self.get_serializer(high_fatigue, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def crew_status(self, request):
        """Get current fatigue status for all crew members"""
        latest_logs = {}
        for log in self.get_queryset().order_by('-duty_start'):
            if log.crew_member.id not in latest_logs:
                latest_logs[log.crew_member.id] = log
        
        serializer = self.get_serializer(list(latest_logs.values()), many=True)
        return Response(serializer.data)


class FlightSwapRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for FlightSwapRequest model"""
    queryset = FlightSwapRequest.objects.select_related(
        'requesting_crew', 'target_crew', 'requesting_flight', 'target_flight'
    ).all()
    serializer_class = FlightSwapRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'requesting_crew', 'target_crew']
    search_fields = ['requesting_crew__username', 'target_crew__username', 'reason']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        """Get pending swap requests"""
        pending = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """Approve a swap request"""
        swap_request = self.get_object()
        swap_request.status = 'approved'
        swap_request.approved_by = request.user
        swap_request.save()
        
        # Here you would implement the actual swap logic
        # For now, just return the updated request
        serializer = self.get_serializer(swap_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        """Reject a swap request"""
        swap_request = self.get_object()
        swap_request.status = 'rejected'
        swap_request.save()
        
        serializer = self.get_serializer(swap_request)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for Alert model"""
    queryset = Alert.objects.select_related('flight', 'created_by').prefetch_related('recipients').all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'severity', 'is_active', 'flight']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']

    
    
    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """Get active alerts"""
        active = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_severity(self, request):
        """Get alerts grouped by severity"""
        severities = {}
        for choice in Alert.SEVERITY_CHOICES:
            severity_code, severity_name = choice
            alerts = self.get_queryset().filter(severity=severity_code, is_active=True)
            serializer = self.get_serializer(alerts, many=True)
            severities[severity_name] = serializer.data
        return Response(severities)
    
    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        """Deactivate an alert"""
        alert = self.get_object()
        alert.is_active = False
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class AlertRecipientViewSet(viewsets.ModelViewSet):
    """ViewSet for AlertRecipient model"""
    queryset = AlertRecipient.objects.select_related('alert', 'recipient').all()
    serializer_class = AlertRecipientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'sms_sent', 'recipient']
    ordering_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def my_alerts(self, request):
        """Get alerts for the current user"""
        user_alerts = self.get_queryset().filter(recipient=request.user)
        serializer = self.get_serializer(user_alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread alerts for current user"""
        count = self.get_queryset().filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark an alert as read"""
        alert_recipient = self.get_object()
        alert_recipient.is_read = True
        alert_recipient.read_at = timezone.now()
        alert_recipient.save()
        
        serializer = self.get_serializer(alert_recipient)
        return Response(serializer.data)