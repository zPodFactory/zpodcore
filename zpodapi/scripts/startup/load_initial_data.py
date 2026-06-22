#!/usr/bin/env python

import secrets

from sqlmodel import func, select

from zpodapi import settings
from zpodapi.lib import database
from zpodcommon import models as M
from zpodcommon.enums import UserStatus

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
            description="Set debug verbosity level on zPodfactory",
            value="INFO",
        )
        session.add(setting_debug)

        setting_domain = M.Setting(
            name="zpodfactory_default_domain",
            description="Default domain for all zPods",
            value="zpodfactory.io",
        )
        session.add(setting_domain)

        setting_broadcom_token = M.Setting(
            name="zpodfactory_broadcom_download_token",
            description="Broadcom Support Portal Generated Download Token",
            value="",
        )
        session.add(setting_broadcom_token)

        settings_ssh_key = M.Setting(
            name="zpodfactory_ssh_key",
            description="Public SSH Key to be pushed on zPod components",
            value="",
        )
        session.add(settings_ssh_key)

        setting_esxi_hostname_is_fqdn = M.Setting(
            name="ff_esxi_hostname_is_fqdn",
            description="William Lam VMware ESXi OVA Templates support",
            value="true",
        )
        session.add(setting_esxi_hostname_is_fqdn)

        setting_endpoint_ova_staging = M.Setting(
            name="ff_endpoint_ova_staging",
            description="Stage L1 OVAs as templates and clone per deployment (Experimental) - Faster & optimized flow when deploying many zPods",
            value="false",
        )
        session.add(setting_endpoint_ova_staging)

        setting_reuse_zpod_password = M.Setting(
            name="ff_reuse_zpod_password",
            description="Preserve password on same-name zPod redeploy so browsers and password-managers entries don't need updating. Great for testing/QA/validations use cases",
            value="false",
        )
        session.add(setting_reuse_zpod_password)

        # Commit all settings
        session.commit()
