import json
from functools import cached_property
from typing import Literal

from sqlmodel import Field

from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin


class Component(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    component_uid: str = Field(..., unique=True, nullable=False)
    component_name: str = Field(..., unique=False, nullable=False)
    component_version: str = Field(..., unique=False, nullable=False)
    component_description: str = Field(..., unique=False, nullable=False)
    library_name: str = Field(default=None, foreign_key="libraries.name", nullable=True)
    filename: str = Field(..., unique=False, nullable=False)
    jsonfile: str = Field(..., unique=False, index=True, nullable=False)
    status: str = Field(..., nullable=True)
    download_status: str = Field(..., nullable=True)
    file_checksum: str = Field(..., nullable=False)

    @cached_property
    def component_json(self) -> dict:
        # Open Component JSON file
        f = open(self.jsonfile)

        # Load component JSON
        return json.load(f)

    def get_usernames(
        self,
        zpod_domain: str,
    ) -> list[dict[str, str]] | None:
        """Get the usernames for this component based on protocol.

        Args:
            zpod_domain: The domain of the zPod

        Returns:
            list[dict[str, str]]: List of usernames with type (ui or ssh)
        """
        usernames = []

        # Always add SSH user
        usernames.append({"username": "root", "type": "ssh"})

        # UI usernames
        match self.component_name.lower():
            case "cloudbuilder":
                usernames.append({"username": "admin", "type": "ui"})
            case "esxi":
                usernames.append({"username": "root", "type": "ui"})
            case "nsx" | "nsxt" | "nsxv":
                usernames.append({"username": "admin", "type": "ui"})
            case "vcd":
                usernames.append({"username": "administrator", "type": "ui"})
            case "vcda":
                usernames.append({"username": "admin", "type": "ui"})
            case "vcsa":
                usernames.append({"username": f"administrator@{zpod_domain}", "type": "ui"})
            case "vrli":
                usernames.append({"username": "admin", "type": "ui"})
            case "vrops":
                usernames.append({"username": "admin", "type": "ui"})
            case "vyos" | "zbox" | _:
                pass

        return usernames
