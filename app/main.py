"""Root-level Uvicorn compatibility entrypoint.

This module lets the documented development command work from the repository
root:

    uvicorn app.main:app --reload

The real FastAPI application remains in ``backend.app.main``.
"""

from backend.app.main import app

__all__ = ["app"]
