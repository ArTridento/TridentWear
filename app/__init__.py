"""Compatibility package for running Uvicorn from the repository root.

The real FastAPI application package lives in ``backend/app``. Extending this
package path lets ``uvicorn app.main:app --reload`` work from ``D:\TridentWear``
without changing the backend package layout.
"""

from pathlib import Path

_BACKEND_APP = Path(__file__).resolve().parent.parent / "backend" / "app"

if _BACKEND_APP.exists():
    __path__.append(str(_BACKEND_APP))
