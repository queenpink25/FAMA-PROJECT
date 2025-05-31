# alerts/views.py

from .utils import send_sms_alert

def check_and_alert():
    value = 101
    if value > 100:
        send_sms_alert("+256705184054", " Value too high!")

check_and_alert()