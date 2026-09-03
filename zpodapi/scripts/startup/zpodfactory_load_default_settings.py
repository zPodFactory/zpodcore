#!/usr/bin/env python
"""Backfill any missing default Settings rows, on every startup.

Unlike zpodfactory_load_initial_data.py (gated on an empty `users` table,
i.e. only a brand-new install), this runs unconditionally so a zpodfactory
instance upgraded in place also picks up settings introduced by newer code.

Idempotent by construction: existing setting names are fetched once up front,
and any name already present is skipped entirely -- a setting that already
exists is never re-created, updated, or have its value touched, regardless of
whether its current value matches the default or was customized by an admin.
"""

import logging

from sqlmodel import select

from zpodapi.lib import database
from zpodcommon import models as M
from zpodfactory_default_settings import DEFAULT_SETTINGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zpodfactory_load_default_settings")

with database.get_session_ctx() as session:
    existing_names = set(session.exec(select(M.Setting.name)).all())

    created = []
    for entry in DEFAULT_SETTINGS:
        name = entry["name"]
        if name in existing_names:
            logger.info("Setting '%s' already exists, skipping", name)
            continue

        value = entry["value"]
        if callable(value):
            value = value()

        session.add(
            M.Setting(
                name=name,
                description=entry["description"],
                value=value,
            )
        )
        logger.info(
            "Setting '%s' did not exist, created with default value %r", name, value
        )
        created.append(name)

    if created:
        session.commit()
    else:
        logger.info("All default settings already present, skipped.")
