# alerts/utils.py

import africastalking

username = "queenalert"
api_key = "atsk_9cdd3d99ce403e499a39a73b395f1746a23853486955eab9e59aadc18659c53b7464136f"
africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_sms_alert(phone_number, message):
    try:
        response = sms.send(message, [phone_number])
        return response
    except Exception as e:
        print("SMS error:", e)
        return None
    
