import json
import os
import subprocess
from pathlib import Path

from prefect import flow, get_run_logger, task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentDownloadStatus, ComponentStatus
from zpodengine.lib import database

PRODUCTS_PATH = "/products"


@task(task_run_name="{filename}-verify-checksum", tags=["atomic_operation"])
def compute_filename_checksum(filename: str) -> str:
    logger = get_run_logger()

    logger.info(f"Computing checksum for {filename}")

    # We assume all our checksums will be sha256 (for now)
    cmd = f"openssl sha256 -r {PRODUCTS_PATH}/{filename}"
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)

    return output.split()[0]


def get_all_components() -> list[M.Component]:
    with database.get_session_ctx() as session:
        components: list[M.Component] = session.exec(select(M.Component)).all()

    return components


@flow(
    name="component_sync",
    log_prints=True,
    flow_run_name="{filename}-sync",
)
def flow_component_sync(filename: str):
    logger = get_run_logger()

    logger.info("Fetch all components from the database")
    # 1. Fetch all components from the database
    components = get_all_components()

    # 2. Compute checksum
    logger.info(f"Checksumming File: {PRODUCTS_PATH}/{filename} ...")
    checksum_task = compute_filename_checksum.submit(filename)
    filename_checksum = checksum_task.result()

    logger.info(f"SHA256 Checksum: {filename_checksum}")

    # 3. validate if checksum exists in one of the components checksum
    #   if yes, mv file, enable the component
    #   if no, unlink file, do nothing

    for c in components:
        # Only check for INACTIVE components
        if c.status == ComponentStatus.INACTIVE:
            _, component_checksum = c.file_checksum.split(":")

            # Only 1 component can match the checksum or none at all
            if component_checksum == filename_checksum:
                logger.info(f"Checksum Matched: {c.component_uid}")

                # Fetch the component's JSON file to grab the official filename
                with open(c.jsonfile) as f:
                    component_json = json.load(f)

                # Depending the download engine, the filename is either:
                # - simple filename: "filename.ova" (customer_connect engine)
                # - URI full path: "https://somewhere/filename.ova" (https engine)

                component_filename = os.path.basename(
                    component_json["component_download_file"]
                )

                # Compute the destination path for the component
                component_path = (
                    Path(PRODUCTS_PATH) / c.component_name / c.component_version
                )

                # Create the component's directory path
                logger.info(f"Creating Component Path: {component_path}")
                component_path.mkdir(parents=True, mode=0o775, exist_ok=True)

                # Move the file to the component's directory
                logger.info(f"Moving file to: {component_path}/{component_filename}")
                os.rename(
                    f"{PRODUCTS_PATH}/{filename}",
                    f"{component_path}/{component_filename}",
                )

                # Set component as ACTIVE/COMPLETED
                logger.info(f"Setting Component: {c.component_uid} to ACTIVE")
                with database.get_session_ctx() as session:
                    component = session.exec(
                        select(M.Component).where(
                            M.Component.component_uid == c.component_uid
                        )
                    ).first()
                    component.status = ComponentStatus.ACTIVE
                    component.download_status = ComponentDownloadStatus.COMPLETED
                    session.add(component)
                    session.commit()

                return component

    # Nothing matched, unlink the file (delete)
    logger.info(f"Checksum not found in any components, unlinking file: {filename}")
    os.unlink(f"{PRODUCTS_PATH}/{filename}")


if __name__ == "__main__":
    flow_component_sync()
