from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', views.CustomUserViewSet, basename='customuser')
router.register(r'crew-profiles', views.CrewProfileViewSet, basename='crewprofile')
router.register(r'flights', views.FlightViewSet, basename='flight')
router.register(r'duty-rosters', views.DutyRosterViewSet, basename='dutyroster')
router.register(r'fatigue-logs', views.FatigueLogViewSet, basename='fatiguelog')
router.register(r'swap-requests', views.FlightSwapRequestViewSet, basename='flightswap')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'alert-recipients', views.AlertRecipientViewSet, basename='alertrecipient')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Authentication
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # API root
    path('api/v1/', include(router.urls)),
    
    # Additional custom endpoints can be added here
    # Example: path('api/v1/custom-endpoint/', views.custom_view, name='custom-endpoint'),
]
