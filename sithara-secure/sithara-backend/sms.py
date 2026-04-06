import os
import threading
from dotenv import load_dotenv
from twilio.rest import Client
 
load_dotenv()
 
ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN  = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_NUM  = os.environ.get('TWILIO_PHONE_NUMBER')
ADMIN_PHONE = os.environ.get('ADMIN_PHONE')
 
client = Client(ACCOUNT_SID, AUTH_TOKEN)
 
 
def _send_sms_async(to, body):
    """Internal: runs in a background thread so it never blocks the request."""
    def _send():
        try:
            client.messages.create(to=to, from_=TWILIO_NUM, body=body)
        except Exception as e:
            print(f'SMS error: {e}')
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
 
 
# ── Public helpers (all non-blocking) ──
 
def notify_admin_order(name, phone, items, address):
    _send_sms_async(ADMIN_PHONE,
        f'New Order!\nFrom: {name} ({phone})\nItems: {items}\nAddress: {address}')
 
def notify_admin_booking(name, phone, date, time, guests):
    _send_sms_async(ADMIN_PHONE,
        f'New Booking!\nName: {name} ({phone})\nDate: {date} at {time}\nGuests: {guests}')
 
def notify_customer_order(phone, status, name):
    msgs = {
        'confirmed': f'Hi {name}, your order at Sithara has been confirmed! We are preparing it now.',
        'delivered': f'Hi {name}, your order has been delivered! Thank you for dining with Sithara.'
    }
    if status in msgs:
        _send_sms_async(f'+91{phone}', msgs[status])
 
def notify_customer_booking(phone, status, name, date, time):
    msgs = {
        'confirmed': f'Hi {name}, your table booking at Sithara for {date} at {time} is confirmed!',
        'cancelled': f'Hi {name}, sorry your booking at Sithara for {date} at {time} has been cancelled.'
    }
    if status in msgs:
        _send_sms_async(f'+91{phone}', msgs[status])