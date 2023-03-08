import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

from prefect import flow, get_run_logger, task
from pydantic import BaseModel
from sqlmodel import select

from zpodcommon import models as M
from zpodengine import settings
from zpodengine.lib import database

LIBRARY_PATH = "/library"
PRODUCTS_PATH = "/products"
BYTE_SIZE = 1024
POWERS = {"KB": 1, "MB": 2, "GB": 3, "TB": 4, "PB": 5}


class ComponentStatus(BaseModel):
    component_name: str
    component_version: str
    component_status: str


class Component(BaseModel):
    component_name: str
    component_version: str
    component_type: Optional[str]
    component_description: Optional[str]
    component_url: Optional[str]
    component_download_engine: str
    component_download_product: Optional[str]
    component_download_subproduct: Optional[str]
    component_download_version: Optional[str]
    component_download_file: Optional[str]
    component_download_file_checksum: Optional[str]  # "sha265:checksum"
    component_download_file_size: str
    component_isnested: Optional[bool]
    component_dst_path: Path | None = None
    component_dl_path: Path | None = None
    component_dl_url: str | None = None
    component_uid: str | None = None


def get_component_record(component_uid: str):
    logger = get_run_logger()
    with database.get_session_ctx() as session:
        component = session.exec(
            select(M.Component).where(M.Component.component_uid == component_uid)
        ).first()
        if component is None:
            logger.warning(f"No component found with UID {component_uid}")
            return None
        else:
            logger.info(f"Found component with UID {component_uid}")
            return component


def update_db(component_uid: str, status: str):
    with database.get_session_ctx() as session:
        component = session.exec(
            select(M.Component).where(M.Component.component_uid == component_uid)
        ).first()
        component.status = status
        session.add(component)
        session.commit()


def get_json_from_file(filename: str):
    if not Path(filename).is_file():
        raise ValueError(f"The provided {filename} does not exist")
    with open(filename, "r") as f:
        return json.load(f)


@task(task_run_name="{component_uid}-request")
def get_component_request(component_uid: str):
    logger = get_run_logger()
    component = get_component_record(component_uid=component_uid)
    logger.info("Extracting raw component details")
    return get_json_from_file(component.filename)


@task(
    retries=3,
    retry_delay_seconds=30,
    task_run_name="{component.component_uid}-download",
)
def download_component(component: Component) -> int:
    logger = get_run_logger()

    cc_cmd = (
        "vcc download"
        " -a"
        f" --user {shlex.quote(settings.VCC_USERNAME)}"
        f" --pass {shlex.quote(settings.VCC_PASSWORD)}"
        f" -p {shlex.quote(component.component_download_product)}"
        f" -s {shlex.quote(component.component_download_subproduct)}"
        f" -v {shlex.quote(component.component_version)}"
        f" -f {shlex.quote(component.component_download_file)}"
        f" -o {shlex.quote(PRODUCTS_PATH)}"
    )
    wget_cmd = f"wget {component.component_dl_url}  -P {PRODUCTS_PATH}"

    cmd = wget_cmd if component.component_download_engine == "https" else cc_cmd

    hidden_pass_cmd = cc_cmd = re.sub(
        r"(--pass\s+)(\S+)", r"\1" + "*" * len(settings.VCC_PASSWORD), cc_cmd
    )
    print_cmd = (
        wget_cmd if component.component_download_engine == "https" else hidden_pass_cmd
    )
    prev_download = Path(PRODUCTS_PATH) / component.component_download_file

    try:
        if prev_download.exists():
            logger.info(
                f"Cleaning previously failed {component.component_uid} download"
            )
            os.remove(prev_download)

        logger.info(
            f"Downloading {component.component_name}-{component.component_version} ..."
        )
        logger.info(f"Executing download command {print_cmd}")
        vcc = subprocess.run(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            check=True,
        )
        if vcc.returncode != 0:
            logger.error(vcc.stderr.decode())
        logger.info(f"{component.component_uid} downloaded")
        return vcc.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading {component.component_uid}")
        logger.error(e)


@task
def get_component(request: dict):
    logger = get_run_logger()
    logger.info("Validating the request. Standby")
    component = Component(**request)

    if component.component_download_engine == "https":
        component.component_dl_url = component.component_download_file
        download_file = urlparse(component.component_download_file).path.split("/")[-1]
        component.component_download_file = download_file

    component.component_uid = (
        f"{component.component_name}-{component.component_version}"
    )
    dst_dir = (
        Path(PRODUCTS_PATH) / component.component_name / component.component_version
    )
    component.component_dst_path = Path(dst_dir) / component.component_download_file
    component.component_dl_path = (
        Path(PRODUCTS_PATH) / component.component_download_file
    )
    logger.info(f"{component.component_uid} validated successfully")
    return component


def get_file_size(component: Component) -> Union[int, None]:
    tmp_dl_path = f"{component.component_dl_path}.tmp"
    if component.component_dl_path.is_file():
        return component.component_dl_path.stat().st_size
    elif tmp_dl_path.is_file():
        return tmp_dl_path.stat().st_size
    return None


def get_size_unit(component: Component) -> Tuple[float, str]:
    size_str, unit_str = component.component_download_file_size.split(" ")
    size = float(size_str)
    unit = unit_str.upper()
    return size, unit


def convert_to_byte(component: Component) -> int:
    size, unit = get_size_unit(component=component)
    return int(size * (BYTE_SIZE ** POWERS[unit]))


def compute_checksum(component: Component, filename: Path) -> str:
    logger = get_run_logger()
    logger.info(f"Computing checksum for {component.component_uid}")
    checksum_str = component.component_download_file_checksum
    checksum_engine = checksum_str.split(":")[0]
    with open(filename, "rb") as f:
        bytes_read = f.read()
        logger.info("Checksum computed")
        return getattr(hashlib, checksum_engine)(bytes_read).hexdigest()


@task(task_run_name="{component.component_uid}-verify-checksum")
def verify_checksum(component: Component, filename: Path) -> bool:
    logger = get_run_logger()

    if not filename.exists():
        logger.info(f"The specified {filename} does not exist")
        raise ValueError(f"{filename} does not exist")

    if (
        component.component_download_file_checksum is None
        and component.component_dl_path.exists()
    ):
        update_db(component_uid=component.component_uid, status="DOWNLOAD_COMPLETE")
        return

    logger.info(f"Verifying {component.component_uid} checksum ...")
    checksum_str = component.component_download_file_checksum
    expected_checksum = checksum_str.split(":")[1]
    checksum = compute_checksum(component, filename)
    if checksum != expected_checksum:
        update_db(component_uid=component.component_uid, status="DOWNLOAD_INCOMPLETE")
        raise ValueError("Checksum does not match")
    logger.info(f"Updating {component.component_uid} status")
    update_db(component_uid=component.component_uid, status="DOWNLOAD_COMPLETE")
    return True


def calculate_percentage(current_size, expected_size):
    return round((100 * current_size / expected_size))


def get_download_paths(component: Component) -> Tuple[str, str]:
    dl_path = component.component_dl_path
    tmp_dl_path = f"{dl_path}.tmp"
    return dl_path, tmp_dl_path


def track_download_progress(dl_path, tmp_dl_path, file_size, timeout=60):
    logger = get_run_logger()
    start_time = time.time()
    logger.info("Tracking dowloading process")
    while not Path(dl_path).exists() and not Path(tmp_dl_path).exists():
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.info("Timeout, waiting for file to track")
            return "Timeout"
        time.sleep(0.5)

    file_path = dl_path if Path(dl_path).exists() else tmp_dl_path

    downloaded_size = Path(file_path).stat().st_size

    progress = calculate_percentage(downloaded_size, file_size)

    return f"{progress}% COMPLETE" if progress < 100 else "DOWNLOAD_COMPLETE"


@task(task_run_name="{component.component_uid}-update-db")
def update_download_progress(component: Component):
    logger = get_run_logger()
    dl_path, tmp_dl_path = get_download_paths(component)
    expected_size = round(convert_to_byte(component=component))
    timeout = 90
    logger.info(f"Tracking {component.component_uid} progress")
    while True:
        progress = track_download_progress(dl_path, tmp_dl_path, expected_size, timeout)
        if progress == "Timeout":
            logger.info("There is no file to track, exiting")
            break

        update_db(
            component_uid=component.component_uid,
            status=progress,
        )
        logger.info(f"{component.component_uid} progress: {progress}")
        if progress == "DOWNLOAD_COMPLETE":
            break
        time.sleep(0.5)


@task(task_run_name="{component.component_uid}-rename")
def rename_file(component: Component):
    logger = get_run_logger()
    logger.info(f"Moving {component.component_uid} to its final destination")
    dst_dir = (
        Path(PRODUCTS_PATH) / component.component_name / component.component_version
    )
    if component.component_dl_path.exists():
        dst_dir.mkdir(parents=True, mode=0o775, exist_ok=True)

    component.component_dl_path.rename(component.component_dst_path)
    if component.component_dst_path.exists():
        logger.info(f"{component.component_uid} renamed")


@flow(log_prints=True, flow_run_name="{component_uid}-download")
def download_component_flow(component_uid: str):
    logger = get_run_logger()

    request = get_component_request(component_uid=component_uid)
    component = get_component(request=request, wait_for=request)
    logger.info(f"Checking if {component.component_uid} exists or not")
    if (
        component.component_dst_path.exists()
        and verify_checksum(
            component,
            component.component_dst_path,
            return_state=True,
        ).is_completed()
    ):
        logger.info(f"{component.component_uid} already exists. Exiting")
        return
    logger.info(
        f"No {component.component_uid} found, will proceed to download the component"
    )
    return_code = download_component(component=component)

    # TODO: Need to revisit this again
    # update_download_progress(component=component)
    if return_code != 0:
        raise ValueError(f"Unable to download {component_uid}")

    verify = verify_checksum(
        component=component,
        filename=component.component_dl_path,
    )

    if return_code == 0 and not verify:
        logger.info(
            f"Incomplete download {component.component_uid} can't verify checksum"
        )

    if return_code == 0 and verify:
        rename_file(component=component, wait_for=verify)


if __name__ == "__main__":
    download_component_flow()
