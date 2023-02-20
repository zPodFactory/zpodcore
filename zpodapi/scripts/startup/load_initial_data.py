#!/usr/bin/env python

import secrets
from datetime import datetime

from zpodapi import settings
from zpodapi.lib import database
from zpodcommon import models as M

with database.get_session_ctx() as session:
    userCnt = session.query(M.User).count()
    if not userCnt:
        # Create a super user with very simple api token for quick tests

        user = M.User(
            username="superuser",
            email="superuser@zpodfactory.io",
            api_token=(
                "supertoken" if settings.DEV_MODE else secrets.token_urlsafe(32)
            ),
            creation_date=datetime.now(),
            last_connection=datetime.now(),
            superadmin=True,
        )

        print(
            f"Initial user created:\n"
            f"  Username: {user.username}\n"
            f"  Email: {user.email}\n"
            f"  API Token: {user.api_token}\n"
        )
        session.add(user)
        session.commit()
