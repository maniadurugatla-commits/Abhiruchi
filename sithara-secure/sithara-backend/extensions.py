"""
extensions.py — Shared Flask extension instances.

Import from here in blueprints to avoid circular imports with app.py.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)
