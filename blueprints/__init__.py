"""RegHub 360 Blueprints."""
from .landing import landing_bp
from .app_views import app_bp
from .api_legacy import api_bp
from .api_demo import api_demo_bp

__all__ = ["landing_bp", "app_bp", "api_bp", "api_demo_bp"]
