from extensions import limiter
from flask import Blueprint, request, jsonify, session
from config import get_connection
from sms import notify_admin_order, notify_customer_order
from routes.validators import validate_order
 
orders_bp = Blueprint('orders', __name__)
 
VALID_STATUSES = ['pending', 'confirmed', 'delivered']
 
# ── Create order ──
@orders_bp.route('/api/order', methods=['POST'])
@limiter.limit("10 per 15 minutes")
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON.'}), 400
 
    errors, clean = validate_order(data)
    if errors:
        return jsonify({'success': False, 'message': errors[0]}), 422
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (full_name, phone, address, items) VALUES (?, ?, ?, ?)",
            (clean['full_name'], clean['phone'], clean['address'], clean['items'])
        )
        conn.commit()
        conn.close()
        notify_admin_order(clean['full_name'], clean['phone'], clean['items'], clean['address'])
        return jsonify({'success': True, 'message': 'Order placed successfully!'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not place order.'}), 500
 
 
# ── Get all orders (admin only) ──
@orders_bp.route('/api/orders', methods=['GET'])
def get_orders():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'data': rows}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not fetch orders.'}), 500
 
 
# ── Update order status (admin only) ──
@orders_bp.route('/api/order/<int:order_id>', methods=['PATCH'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
 
    data   = request.get_json(silent=True)
    status = data.get('status', '').strip() if data else ''
 
    if status not in VALID_STATUSES:
        return jsonify({'success': False, 'message': 'Invalid status.'}), 400
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, phone FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
        conn.close()
        notify_customer_order(order['phone'], status, order['full_name'])
        return jsonify({'success': True, 'message': f'Order status updated to {status}.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not update order.'}), 500
 
 
# ── Delete order (admin only) ──
@orders_bp.route('/api/order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    try:
        conn = get_connection()
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Order deleted.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Could not delete order.'}), 500