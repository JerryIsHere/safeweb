"""WSGI entry point for production hosting such as Render or Gunicorn."""

from web.app import app

if __name__ == "__main__":
    app.run()
