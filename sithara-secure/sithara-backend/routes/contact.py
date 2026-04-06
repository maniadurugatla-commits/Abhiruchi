from extensions import limiter
from flask import Blueprint, request, jsonify, session
from config import get_connection
from routes.validators import validate_contact
 
contact_bp = Blueprint('contact', __name__)
 
# ── Save contact message ──
@contact_bp.route('/api/contact', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def save_message():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON.'}), 400
 
    errors, clean = validate_contact(data)
    if errors:
        return jsonify({'success': False, 'message': errors[0]}), 422
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contact_messages (full_name, email, message) VALUES (?, ?, ?)",
            (clean['full_name'], clean['email'], clean['message'])
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message received! We will get back to you soon.'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not save message.'}), 500
 
 
# ── Get all messages (admin only) ──
@contact_bp.route('/api/contact', methods=['GET'])
def get_messages():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'data': rows}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not fetch messages.'}), 500
 
 
# ── Delete message (admin only) ──
@contact_bp.route('/api/contact/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn = get_connection()
        conn.execute("DELETE FROM contact_messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message deleted.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not delete message.'}), 500