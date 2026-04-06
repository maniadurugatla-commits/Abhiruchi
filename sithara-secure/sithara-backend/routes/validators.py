"""
Input validation helpers for all routes.
Sanitizes, validates, and enforces length bounds before data touches the DB.
"""
import re
from datetime import date as _date
 
 
# ── Helpers ──────────────────────────────────────────────────────────────────
 
def sanitize_str(value, max_len=200, min_len=0):
    """
    Strip whitespace, enforce min/max length.
    Returns the cleaned string, or None if the value fails constraints.
    """
    if not isinstance(value, str):
        return None
    cleaned = value.strip()[:max_len]
    if len(cleaned) < min_len:
        return None
    return cleaned
 
 
def is_valid_phone(phone):
    """Allow 10-digit Indian mobile numbers (optionally prefixed with +91)."""
    return bool(re.fullmatch(r'(\+91)?[6-9]\d{9}', phone.strip()))
 
 
def is_valid_email(email):
    """Simple structural email check — good enough for a restaurant form."""
    return bool(re.fullmatch(r'[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}', email.strip()))
 
 
def is_valid_date(date_str):
    """Expect YYYY-MM-DD; also reject dates in the past."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str.strip()):
        return False
    try:
        year, month, day = map(int, date_str.split('-'))
        booking = _date(year, month, day)
        return booking >= _date.today()
    except ValueError:
        return False
 
 
def is_valid_time(time_str):
    """Expect HH:MM in 24-hour format."""
    if not re.fullmatch(r'\d{2}:\d{2}', time_str.strip()):
        return False
    h, m = map(int, time_str.split(':'))
    return 0 <= h <= 23 and 0 <= m <= 59
 
 
def is_valid_guests(guests):
    """1–50 guests."""
    try:
        n = int(guests)
        return 1 <= n <= 50
    except (ValueError, TypeError):
        return False
 
 
# ── Validators ────────────────────────────────────────────────────────────────
 
def validate_booking(data):
    errors = []
    full_name = sanitize_str(data.get('full_name', ''), max_len=100, min_len=2)
    phone     = sanitize_str(data.get('phone', ''),     max_len=15)
    date      = sanitize_str(data.get('date', ''),      max_len=10)
    time      = sanitize_str(data.get('time', ''),      max_len=5)
    guests    = data.get('guests')
 
    if not full_name:                    errors.append('Full name must be 2–100 characters.')
    if not phone:                        errors.append('Phone is required.')
    elif not is_valid_phone(phone):      errors.append('Invalid phone number (10-digit Indian mobile).')
    if not date:                         errors.append('Date is required.')
    elif not is_valid_date(date):        errors.append('Invalid or past date (use YYYY-MM-DD).')
    if not time:                         errors.append('Time is required.')
    elif not is_valid_time(time):        errors.append('Invalid time (use HH:MM, 24-hour).')
    if guests is None:                   errors.append('Guests count is required.')
    elif not is_valid_guests(guests):    errors.append('Guests must be between 1 and 50.')
 
    return errors, {
        'full_name': full_name,
        'phone': phone,
        'date': date,
        'time': time,
        'guests': int(guests) if guests and not errors else None
    }
 
 
def validate_order(data):
    errors = []
    full_name = sanitize_str(data.get('full_name', ''), max_len=100, min_len=2)
    phone     = sanitize_str(data.get('phone', ''),     max_len=15)
    address   = sanitize_str(data.get('address', ''),   max_len=300, min_len=10)
    items     = sanitize_str(data.get('items', ''),     max_len=1000, min_len=3)
 
    if not full_name:                errors.append('Full name must be 2–100 characters.')
    if not phone:                    errors.append('Phone is required.')
    elif not is_valid_phone(phone):  errors.append('Invalid phone number (10-digit Indian mobile).')
    if not address:                  errors.append('Address must be at least 10 characters.')
    if not items:                    errors.append('Order items must be at least 3 characters.')
 
    return errors, {
        'full_name': full_name,
        'phone': phone,
        'address': address,
        'items': items
    }
 
 
def validate_contact(data):
    errors = []
    full_name = sanitize_str(data.get('full_name', ''), max_len=100, min_len=2)
    email     = sanitize_str(data.get('email', ''),     max_len=150)
    message   = sanitize_str(data.get('message', ''),   max_len=2000, min_len=10)
 
    if not full_name:                 errors.append('Full name must be 2–100 characters.')
    if not email:                     errors.append('Email is required.')
    elif not is_valid_email(email):   errors.append('Invalid email address.')
    if not message:                   errors.append('Message must be 10–2000 characters.')
 
    return errors, {
        'full_name': full_name,
        'email': email,
        'message': message
    }