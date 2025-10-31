# WSGI entrypoint for production servers (gunicorn)
from app import app

# Optional alias for some hosts
application = app
