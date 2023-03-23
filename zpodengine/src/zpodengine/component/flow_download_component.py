import json
import os
import re
import shlex
import subprocess
import time
from enum import Enum
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


class DownloadState(Enum):
    FAILED_DOWNLOAD = 0
    NOT_ENTITLED = 1
    DOWNLOAD_COMPLETE = 2
    FAILED_AUTHENTICATION = 3
    DOWNLOAD_INCOMPLETE = 4
    SCHEDULED = 5


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


def get_component_record(uid: str):
    logger = get_run_logger()
    component = get_component_by_uid(uid=uid)
    if component is None:
        logger.warning(f"No component found with UID {uid}")
        return None
    else:
        logger.info(f"Found component with UID {uid}")
        return component


def get_component_by_uid(uid: str) -> M.Component:
    with database.get_session_ctx() as session:
        return session.exec(
            select(M.Component).where(M.Component.component_uid == uid)
        ).first()


def update_db(uid: str, status: str):
    component = get_component_by_uid(uid)
    component.status = status
    with database.get_session_ctx() as session:
        session.add(component)
        session.commit()


def get_json_from_file(filename: str):
    if not Path(filename).is_file():
        raise ValueError(f"The provided {filename} does not exist")
    with open(filename, "r") as f:
        return json.load(f)


@task(task_run_name="{uid}-request")
def get_component_request(uid: str):
    logger = get_run_logger()
    component = get_component_record(uid)
    logger.info("Extracting raw component details")
    return get_json_from_file(component.filename)


def run_command(cmd: str, cmd_engine: str):
    if cmd_engine == "cc":
        return subprocess.Popen(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
    else:
        return subprocess.run(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            check=True,
        )


@task(
    task_run_name="{component.component_uid}-download",
    tags=["download"],
)
def download_component(component: Component) -> int:
    logger = get_run_logger()
    failed_message = "FAILED_DOWNLOAD"
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

    cmd_engine = "wget" if component.component_download_engine == "https" else "cc"

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

        process = run_command(cmd=cmd, cmd_engine=cmd_engine)

        while cmd_engine == "cc" and process.poll() is None:
            process.stdout.readline()

        return_code = process.wait() if cmd_engine == "cc" else process.returncode
        if return_code != 0:
            msg = (
                process.stderr.read().decode().strip()
                if cmd_engine == "cc"
                else process.stdout.decode()
            )
            logger.info(f"stderr: {msg}")
            if "Authentication failure" in msg:
                logger.error(msg)
                raise RuntimeError("AuthenticationError")
            if "You are not entitled" in msg:
                raise RuntimeError("EntitlementError")
        else:
            logger.info(f"{component.component_uid} downloaded")
            return 0
    except RuntimeError as e:
        if e.args[0] == "AuthenticationError":
            update_db(component.component_uid, DownloadState.FAILED_AUTHENTICATION.name)
            logger.error("The provided credentials are not correct.")
            raise e
        if e.args[0] == "EntitlementError":
            update_db(component.component_uid, DownloadState.NOT_ENTITLED.name)
            logger.error("You are not entitled to download this sub-product")
            raise e
    except Exception as e:
        logger.error(f"Error downloading {component.component_uid}")
        update_db(component.component_uid, failed_message)
        logger.error(e)
        raise e


@task(task_run_name="{uid}-get")
def get_component(request: dict, uid: str):
    logger = get_run_logger()
    logger.info(f"Validating the request {uid}. Standby")
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
    checksum_type = checksum_str.split(":")[0]
    cmd = f"openssl {checksum_type} -r {filename}"
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output.split()[0]


@task(task_run_name="{component.component_uid}-verify-checksum")
def verify_checksum(component: Component, filename: Path) -> bool:
    logger = get_run_logger()
    if not filename.exists():
        logger.info(f"The specified {filename} does not exist")
        raise ValueError(f"{filename} does not exist")

    if component.component_download_file_checksum is None:
        if component.component_dl_path.exists():
            update_db(
                uid=component.component_uid, status=DownloadState.DOWNLOAD_COMPLETE.name
            )
        return

    logger.info(f"Verifying {component.component_uid} checksum ...")
    checksum_str = component.component_download_file_checksum
    expected_checksum = checksum_str.split(":")[1]
    checksum = compute_checksum(component, filename)
    logger.info(f"Checksum: {checksum}")
    if checksum != expected_checksum:
        update_db(
            uid=component.component_uid, status=DownloadState.DOWNLOAD_INCOMPLETE.name
        )
        raise ValueError("Checksum does not match")
    logger.info(f"Updating {component.component_uid} status")
    update_db(uid=component.component_uid, status=DownloadState.DOWNLOAD_COMPLETE.name)
    return True


def calculate_percentage(current_size, expected_size):
    return round((100 * current_size / expected_size))


def get_download_paths(component: Component) -> Tuple[str, str]:
    dl_path = component.component_dl_path
    tmp_dl_path = f"{dl_path}.tmp"
    return dl_path, tmp_dl_path


def track_download_progress(dl_path, tmp_dl_path, file_size, timeout=30):
    logger = get_run_logger()
    start_time = time.time()
    logger.info("Tracking dowloading process")
    while not Path(dl_path).exists() and not Path(tmp_dl_path).exists():
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.info("Timeout, waiting for file to track")
            return "Timeout"
        time.sleep(1)

    file_path = dl_path if Path(dl_path).exists() else tmp_dl_path

    downloaded_size = Path(file_path).stat().st_size

    progress = calculate_percentage(downloaded_size, file_size)

    return f"{progress}" if progress < 100 else "DOWNLOAD_COMPLETE"


@task(task_run_name="{component.component_uid}-update-db")
def update_download_progress(component):
    logger = get_run_logger()
    dl_path, tmp_dl_path = get_download_paths(component)
    expected_size = round(convert_to_byte(component=component))
    timeout = 30
    success = False

    logger.info(f"Tracking download progress for component {component.component_uid}")

    while True:
        progress = track_download_progress(dl_path, tmp_dl_path, expected_size, timeout)
        if progress == "Timeout":
            logger.info("Timeout: no file to track, exiting")
            break

        current_state = get_component_by_uid(component.component_uid).status
        if current_state in (
            DownloadState.FAILED_AUTHENTICATION.name,
            DownloadState.FAILED_DOWNLOAD.name,
            DownloadState.NOT_ENTITLED.name,
            DownloadState.DOWNLOAD_COMPLETE.name,
        ):
            logger.error(
                f"Cannot track {component.component_uid} - state {current_state}"
            )
            raise RuntimeError("Failed Download")

        update_db(uid=component.component_uid, status=progress)
        logger.info(
            f"Download progress for component {component.component_uid}: {progress}%"
        )

        if progress == "DOWNLOAD_COMPLETE":
            success = True
            break

        time.sleep(10)

    logger.info(
        f"Finished tracking download progress for component {component.component_uid}"
    )
    return success


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


@flow(log_prints=True, flow_run_name="{uid}-download")
def flow_download_component(uid: str):
    logger = get_run_logger()
    request = get_component_request(uid=uid)
    logger.info(f"Request: {request}")
    component = get_component(request=request, uid=uid, wait_for=request)
    logger.info(f"Checking if {component.component_uid} exists or not")

    if (
        component.component_dst_path.exists()
        and verify_checksum(
            component,
            component.component_dst_path,
            return_state=True,
        ).is_completed()
    ):
        logger.info(f"{uid} already exists. Exiting")
        return
    logger.info(f"No {uid} found, will proceed to download the component")
    download_component.submit(component=component)

    status_task = update_download_progress.submit(component=component)
    result = status_task.result()

    logger.info(f"Status: {result}")

    if not result:
        raise ValueError(f"Unable to download {uid}")

    verify = verify_checksum(
        component=component,
        filename=component.component_dl_path,
        wait_for=result,
    )

    if result and not verify:
        logger.info(
            f"Incomplete download {component.component_uid} can't verify checksum"
        )

    if result and verify:
        rename_file(component=component, wait_for=verify)


if __name__ == "__main__":
    flow_download_component()
