#!/usr/bin/env python

import secrets

from zpodapi import settings
from zpodapi.lib import database
from zpodcommon import models as M
from zpodcommon.enums import UserStatus

with database.get_session_ctx() as session:
    userCnt = session.query(M.User).count()
    if not userCnt:
        # Create a super user with very simple api token for quick tests

        user = M.User(
            username="superuser",
            email="superuser@zpodfactory.io",
            api_token=secrets.token_urlsafe(32),
            superadmin=True,
            status=UserStatus.ACTIVE,
        )

        print(
            f"Initial user created:\n"
            f"  Username: {user.username}\n"
            f"  Email: {user.email}\n"
            f"  API Token: {user.api_token}\n"
        )
        session.add(user)

        #
        # Adding Default settings value for the whole zPodFactory Instance
        # Settings Permissions = superadmin ONLY
        # Right now the topology of this VM is:
        # - eth0 public ip
        # - eth1 private ip
        # This might change to a single Nic (eth0)
        #

        # TODO: We are in a docker container here, this will not work.
        private_ip_zpodfactory = settings.HOST
        setting_zpodfactory_hostip = M.Setting(
            name="zpodfactory_host",
            description="zpodfactory host address (NTP, ISO Datastore, etc)",
            value=private_ip_zpodfactory,
        )
        session.add(setting_zpodfactory_hostip)

        setting_debug = M.Setting(
            name="zpodfactory_debug_level",
            description="Set debug verbosity level on zPodfactory instance",
            value="INFO",
        )
        session.add(setting_debug)

        setting_domain = M.Setting(
            name="zpodfactory_instances_domain",
            description="Default domain for all zPods",
            value="zpodfactory.io",
        )
        session.add(setting_domain)

        setting_cc_username = M.Setting(
            name="zpodfactory_customerconnect_username",
            description="VMware Customer Connect user account",
            value="user@xyz.com",
        )
        session.add(setting_cc_username)

        setting_cc_password = M.Setting(
            name="zpodfactory_customerconnect_password",
            description="VMware Customer Connect user password",
            value="amazingpassword",
        )
        session.add(setting_cc_password)

        settings_ssh_key = M.Setting(
            name="zpodfactory_ssh_key",
            description="Public SSH Key to be pushed on instance/components",
            value="",
        )
        session.add(settings_ssh_key)

        # Commit all settings
        session.commit()
