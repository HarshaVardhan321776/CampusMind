import sys
import os

# Add Backend directory to sys.path so app imports work seamlessly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "Backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app

# Expose app for Vercel ASGI serverless handler
handler = app

