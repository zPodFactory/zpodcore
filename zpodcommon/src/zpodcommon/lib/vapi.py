import requests
from rich.console import Console
from vmware.vapi.lib.connect import get_requests_connector
from vmware.vapi.security.session import create_session_security_context
from vmware.vapi.security.user_password import create_user_password_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
from vmware.vapi.vsphere.client import Session, create_vsphere_client

console = Console()


class VAPIClient:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.stub_config = self.get_stub_config()
       

    def get_stub_config(self, vclient_only: bool = False):
        api_url = f"https://{self.hostname}/api"
        requests.packages.urllib3.disable_warnings()
        session = requests.session()
        session.verify = False

        # return vcenter client
        if vclient_only:
            return create_vsphere_client(
                username=self.username,
                password=self.password,
                server=self.hostname,
                session=session,
            )

        security_context = create_user_password_security_context(
            self.username, self.password
        )
        connector = get_requests_connector(
            session=session,
            url=api_url,
        )
        connector.set_security_context(security_context)
        session_service = Session(
            StubConfigurationFactory.new_std_configuration(connector)
        )

        session_id = session_service.create()
        security_context = create_session_security_context(session_id)

        connector = get_requests_connector(
            session=session,
            url=api_url,
        )
        connector.set_security_context(security_context)
        return StubConfigurationFactory.new_std_configuration(connector)

