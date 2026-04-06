import os
from flask import Flask, session, request, redirect, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from config import init_db
from extensions import limiter
 
# ── Load environment variables from .env ──
load_dotenv()
 
app = Flask(__name__)
 
# ── Secret key — MUST be set via env; no insecure fallback ──
_secret = os.environ.get('FLASK_SECRET_KEY')
if not _secret:
    raise RuntimeError("FLASK_SECRET_KEY is not set. Add it to your .env file.")
app.secret_key = _secret
 
# ── Reject payloads larger than 64 KB ──
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024  # 64 KB
 
# ── Secure session cookie settings ──
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE']   = os.environ.get('FLASK_ENV') == 'production'
 
# ── CORS: restrict to configured origin only ──
_allowed_origin = os.environ.get('ALLOWED_ORIGIN', 'http://localhost:5000')
CORS(app, origins=[_allowed_origin])
 
# ── Rate Limiting ──
limiter.init_app(app)
 
# ── Admin credentials from environment ──
ADMIN_USERNAME      = os.environ.get('ADMIN_USERNAME')
_raw_password       = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_USERNAME or not _raw_password:
    raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env")
ADMIN_PASSWORD_HASH = generate_password_hash(_raw_password)
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
# ── Register blueprints ──
from routes.bookings import bookings_bp
from routes.orders   import orders_bp
from routes.menu     import menu_bp
from routes.contact  import contact_bp
 
app.register_blueprint(bookings_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(contact_bp)
 
 
# ── HTTP Security Headers ──
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options']  = 'nosniff'
    response.headers['X-Frame-Options']         = 'DENY'
    response.headers['X-XSS-Protection']        = '1; mode=block'
    response.headers['Referrer-Policy']         = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:;"
    )
    return response
 
 
# ── 413 handler: payload too large ──
@app.errorhandler(413)
def payload_too_large(e):
    return jsonify({'success': False, 'message': 'Request payload is too large.'}), 413
 
 
# ── 429 handler: rate limit exceeded ──
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return jsonify({
        'success': False,
        'message': f'Too many requests. {str(e.description)}'
    }), 429
 
 
@app.route('/')
def index():
    return send_from_directory('..', 'index.html')
 
@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('../images', filename)
 
@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect('/login')
    return send_from_directory(BASE_DIR, 'admin.html')
 
@app.route('/login')
def login_page():
    if session.get('admin_logged_in'):
        return redirect('/admin')
    return send_from_directory(BASE_DIR, 'login.html')
 
@app.route('/admin/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def admin_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400
 
    username = str(data.get('username', '')).strip()[:80]
    password = str(data.get('password', ''))[:200]
 
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session['admin_logged_in'] = True
        session.permanent = False
        return jsonify({'success': True})
 
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
 
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/login')
 
 
if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)