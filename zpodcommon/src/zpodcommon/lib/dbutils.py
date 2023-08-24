import re

from sqlalchemy import exc
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.lib import database


# Examples:
# Behaviour for matching the most precise block in a component versioning.
# component_uid "vcsa-8.0u1c" will output: ['vcsa-8', 'vcsa-8.0', 'vcsa-8.0u1', 'vcsa-8.0u1c']
# component_uid "nsx-4.1.1.0" will output: ['nsx-4', 'nsx-4.1', 'nsx-4.1.1', 'nsx-4.1.1.0']
# This will allow to check for licenses per specific VMware version
#
def get_component_license_groups(component_uid: str):
    # Base pattern to match the product and major version
    base_pattern = re.compile(r"(\w+)-(\d+)")
    # Pattern to match the remaining sections
    remaining_pattern = re.compile(r"(\.\d+|u\d+|[a-z])")
    # Pattern to match specific patterns like "-onprem" or "-cloud"
    special_pattern = re.compile(r"-(onprem|cloud)")

    base_match = base_pattern.match(component_uid)
    if not base_match:
        return "No match found!"

    base = f"{base_match[1]}-{base_match[2]}"
    results = [base]

    remaining = component_uid[len(base) :]
    while remaining:
        remaining_match = remaining_pattern.match(remaining)
        if remaining_match:
            base += remaining_match[1]
            results.append(base)
            remaining = remaining[len(remaining_match[1]) :]

        # Check for special patterns
        special_match = special_pattern.match(remaining)
        if special_match:
            base += special_match[0]
            results.append(base)
            remaining = remaining[len(special_match[0]) :]

        if not remaining_match and not special_match:
            break

    # print(f"Component License Groups: {results}")
    return results


def find_matching_license(component_groups: list, licenses: list, license_type: str):
    print(f"Component groups: {component_groups}")
    if not component_groups:
        return None

    lic_group = component_groups.pop()
    # print(f"Checking for component license: {lic_group}")
    for lic in licenses:
        # print(f" - Checking license: {lic.name}...")
        if f"{lic_group}_{license_type}" in lic.name:
            # print(f"*** FOUND LICENSE MATCH: {lic.value} ***")
            return lic.value

    # print("No match found, trying again...")
    return find_matching_license(component_groups, licenses, license_type)


class DBUtils:
    #
    # DB helper class to query things easily.
    #

    @classmethod
    def get_setting_value(cls, name: str):
        with database.get_session_ctx() as session:
            try:
                setting = session.exec(
                    select(M.Setting).where(M.Setting.name == name)
                ).one()
                return setting.value
            except exc.NoResultFound:
                return None

    @classmethod
    def get_setting_licenses(cls):
        with database.get_session_ctx() as session:
            try:
                settings = session.exec(select(M.Setting))
                return [entry for entry in settings if "license_" in entry.name]
            except exc.NoResultFound:
                return None

    @classmethod
    def get_component_license(cls, component: M.Component, license_type: str):
        print(
            f"Checking component license: {component.component_uid} with type {license_type}"
        )

        # Fetch all licenses available in Settings
        licenses = cls.get_setting_licenses()

        # Return the most specific license based on component_uid
        return find_matching_license(
            get_component_license_groups(component.component_uid),
            licenses,
            license_type,
        )
