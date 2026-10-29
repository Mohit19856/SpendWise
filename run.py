"""
SpendWise entry point.

Local development:
    python run.py

Production (AWS EC2, Linux):
    gunicorn --bind 127.0.0.1:8000 "run:app"

The Flask development server used by "python run.py" is for local
development/demo only - it must never be exposed to the public internet.
"""

import os

from app import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "development"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # host="127.0.0.1" keeps the dev server reachable from your own laptop only.
    app.run(host="127.0.0.1", port=port, debug=app.config.get("DEBUG", False))
