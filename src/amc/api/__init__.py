"""API package for AMC.

Exposes a single ``api_router`` that aggregates the unversioned health router
(used by load balancers and Kubernetes probes) and the versioned ``/api/v1``
surface. Domain routers (auth, catalog, attempts, progress) are added to
``v1_router`` as they are implemented.
"""

from __future__ import annotations

from fastapi import APIRouter

from amc.api.health import router as health_router

# Versioned API surface. Domain routers declare their own sub-prefix and tags
# and are included here as they come online.
v1_router = APIRouter(prefix="/api/v1")

# Top-level aggregate mounted by the app factory.
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router)

__all__ = ["api_router", "health_router", "v1_router"]
