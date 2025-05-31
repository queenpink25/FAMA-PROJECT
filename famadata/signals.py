# alerts/signals.py

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Alert, AlertRecipient
from alerts.utils import send_sms_alert

@receiver(m2m_changed, sender=Alert.recipients.through)
def send_sms_to_recipients(sender, instance, action, **kwargs):
    if action == "post_add":
        alert = instance
        for user in alert.recipients.all():
            phone = getattr(user, "phone_number", None)
            if phone:
                # Check if SMS was already sent
                ar, created = AlertRecipient.objects.get_or_create(alert=alert, recipient=user)
                if not ar.sms_sent:
                    message = f"🚨 {alert.title}\n{alert.message}"
                    response = send_sms_alert(phone, message)
                    ar.sms_sent = True
                    ar.sms_delivery_status = "sent" if response else "failed"
                    ar.save()
