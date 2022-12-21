#!/usr/bin/env python

import secrets
from datetime import datetime

from zpodapi.lib import database
from zpodapi.models import User

session = database.get_session_one()
userCnt = session.query(User).count()
if not userCnt:
    user = User(
        username="superuser",
        email="superuser@zpodfactory.io",
        api_token=secrets.token_urlsafe(256),
        creation_date=datetime.now(),
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
