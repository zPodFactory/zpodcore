#!/usr/bin/env python

import logging
import secrets

from sqlmodel import func, select

from zpodapi.lib import database
from zpodcommon import models as M
from zpodcommon.enums import UserStatus
from zpodfactory_default_settings import DEFAULT_SETTINGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zpodfactory_load_initial_data")

with database.get_session_ctx() as session:
    userCnt = session.exec(select(func.count(M.User.id))).one()
    if not userCnt:
        # Create a super user with very simple api token for quick tests
        user = M.User(
            username="superuser",
            email="superuser@zpodfactory.io",
            api_token=secrets.token_urlsafe(32),
            superadmin=True,
            status=UserStatus.ENABLED,
        )

        print(
            f"Initial user created:\n"
            f"  Username: {user.username}\n"
            f"  Email: {user.email}\n"
            f"  API Token: {user.api_token}\n"
        )
        session.add(user)

        # Default settings value for the whole zPodFactory Instance.
        # Settings Permissions = superadmin ONLY.
        # The DB is empty at this point (userCnt == 0), so every default
        # setting is created unconditionally here -- see
        # zpodfactory_default_settings.py for the shared list. Any setting
        # added by a later code version still gets backfilled onto
        # already-running instances by zpodfactory_load_default_settings.py,
        # which runs on every startup.
        for entry in DEFAULT_SETTINGS:
            value = entry["value"]
            if callable(value):
                value = value()
            session.add(
                M.Setting(
                    name=entry["name"],
                    description=entry["description"],
                    value=value,
                )
            )
            logger.info(
                "Setting '%s' created with default value %r", entry["name"], value
            )

        # Commit user + all settings
        session.commit()
    else:
        logger.info(
            "Users already exist (%d), skipping initial user/settings seed", userCnt
        )
