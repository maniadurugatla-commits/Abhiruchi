from flask import Blueprint, request, jsonify, session
from config import get_connection
from extensions import limiter
 
menu_bp = Blueprint('menu', __name__)
 
 
def _require_admin():
    """Return a 401 response tuple if not logged in, else None."""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
    return None
 
 
def _sanitize(value, max_len=200):
    if not isinstance(value, str):
        return None
    return value.strip()[:max_len] or None
 
 
# ── Get all active menu items ──
@menu_bp.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menu WHERE is_active = 1 ORDER BY category, name")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'data': rows}), 200
    except Exception:
        return jsonify({'success': False, 'message': 'Could not fetch menu.'}), 500
 
 
# ── Add a new menu item (admin only) ──
@menu_bp.route('/api/menu', methods=['POST'])
@limiter.limit("30 per hour")
def add_menu_item():
    guard = _require_admin()
    if guard:
        return guard
 
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON.'}), 400
 
    name        = _sanitize(data.get('name', ''), 100)
    description = _sanitize(data.get('description', ''), 500)
    image_path  = _sanitize(data.get('image_path', ''), 200)
    category    = _sanitize(data.get('category', 'main'), 50)
 
    try:
        price = float(data.get('price', 0))
        if price <= 0 or price > 100000:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid price.'}), 400
 
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400
 
    valid_categories = {'starter', 'main', 'dessert', 'drink'}
    if category not in valid_categories:
        return jsonify({'success': False, 'message': f'Category must be one of: {", ".join(valid_categories)}'}), 400
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO menu (name, price, description, image_path, category) VALUES (?, ?, ?, ?, ?)",
            (name, price, description, image_path, category)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Menu item added!'}), 201
    except Exception:
        return jsonify({'success': False, 'message': 'Could not add menu item.'}), 500
 
 
# ── Update a menu item (admin only) ──
@menu_bp.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    guard = _require_admin()
    if guard:
        return guard
 
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON.'}), 400
 
    name        = _sanitize(data.get('name', ''), 100)
    description = _sanitize(data.get('description', ''), 500)
    image_path  = _sanitize(data.get('image_path', ''), 200)
    category    = _sanitize(data.get('category', 'main'), 50)
 
    try:
        price = float(data.get('price', 0))
        if price <= 0 or price > 100000:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid price.'}), 400
 
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE menu
            SET name=?, price=?, description=?, image_path=?, category=?
            WHERE id=?
        """, (name, price, description, image_path, category, item_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Menu item updated!'}), 200
    except Exception:
        return jsonify({'success': False, 'message': 'Could not update menu item.'}), 500
 
 
# ── Delete (deactivate) a menu item (admin only) ──
@menu_bp.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    guard = _require_admin()
    if guard:
        return guard
 
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE menu SET is_active = 0 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Menu item removed.'}), 200
    except Exception:
        return jsonify({'success': False, 'message': 'Could not remove menu item.'}), 500