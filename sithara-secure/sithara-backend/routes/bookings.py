from extensions import limiter
from flask import Blueprint, request, jsonify, session
from config import get_connection
from sms import notify_admin_booking
from routes.validators import validate_booking
 
bookings_bp = Blueprint('bookings', __name__)
 
# ── Create booking ──
@bookings_bp.route('/api/booking', methods=['POST'])
@limiter.limit("10 per 15 minutes")
def create_booking():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON.'}), 400
 
    errors, clean = validate_booking(data)
    if errors:
        return jsonify({'success': False, 'message': errors[0]}), 422
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookings (full_name, phone, date, time, guests) VALUES (?, ?, ?, ?, ?)",
            (clean['full_name'], clean['phone'], clean['date'], clean['time'], clean['guests'])
        )
        conn.commit()
        conn.close()
        notify_admin_booking(clean['full_name'], clean['phone'], clean['date'], clean['time'], clean['guests'])
        return jsonify({'success': True, 'message': 'Booking confirmed!'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not save booking.'}), 500
 
 
# ── Get all bookings (admin only) ──
@bookings_bp.route('/api/bookings', methods=['GET'])
def get_bookings():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'data': rows}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not fetch bookings.'}), 500
 
 
# ── Delete booking (admin only) ──
@bookings_bp.route('/api/booking/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn = get_connection()
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Booking deleted.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not delete booking.'}), 500