"""API package for AMC.

Exposes a single ``api_router`` that aggregates the unversioned health router
(used by load balancers and Kubernetes probes) and the versioned ``/api/v1``
surface. Domain routers (auth, catalog, attempts, progress) are added to
``v1_router`` as they are implemented.
"""

from __future__ import annotations

from fastapi import APIRouter

from amc.api.attempts import router as attempts_router
from amc.api.auth import router as auth_router
from amc.api.catalog import router as catalog_router
from amc.api.health import router as health_router
from amc.api.invites import router as invites_router
from amc.api.progress import router as progress_router

# Versioned API surface. Each domain router declares its own sub-prefix and tags.
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(invites_router)
v1_router.include_router(catalog_router)
v1_router.include_router(attempts_router)
v1_router.include_router(progress_router)

# Top-level aggregate mounted by the app factory.
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router)

__all__ = ["api_router", "health_router", "v1_router"]
