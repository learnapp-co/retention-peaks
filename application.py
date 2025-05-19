# application.py
from src.main import app

# Directly expose FastAPI app as `application` for Gunicorn (ASGI)
application = app
