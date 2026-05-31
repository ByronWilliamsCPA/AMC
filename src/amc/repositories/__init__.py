"""Async data-access repositories for AMC.

Repositories encapsulate SQLAlchemy queries per aggregate so routers and services
stay free of ORM details. Each repository takes an ``AsyncSession`` and exposes
intention-revealing methods rather than raw query builders.
"""

from __future__ import annotations
