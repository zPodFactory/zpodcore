import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from prefect import flow, get_run_logger, task
from pydantic import BaseModel
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentDownloadStatus, ComponentStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodengine.lib import database

LIBRARY_PATH = "/library"
PRODUCTS_PATH = "/products"
BYTE_SIZE = 1024
POWERS = {"KB": 1, "MB": 2, "GB": 3, "TB": 4, "PB": 5}


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
    component_download_type: Optional[str]
    component_download_file_checksum: Optional[str]  # "sha265:checksum"
    component_download_file_size: str
    component_isnested: Optional[bool]
    component_dst_path: Path | None = None
    component_dl_path: Path | None = None
    component_dl_url: str | None = None
    component_uid: str | None = None


def get_component_by_uid(uid: str):
    logger = get_run_logger()

    with database.get_session_ctx() as session:
        component = session.exec(
            select(M.Component).where(M.Component.component_uid == uid)
        ).first()

    if component is not None:
        return component
    logger.warning(f"No component found with UID {uid}")
    return None


def update_db(
    uid: str, download_status: str, status: ComponentStatus = ComponentStatus.INACTIVE
):
    if not (component := get_component_by_uid(uid)):
        raise ValueError(f"Component {uid} couldn't be found !")
    component.download_status = download_status
    component.status = status
    with database.get_session_ctx() as session:
        session.add(component)
        session.commit()


def get_json_from_file(filename: str):
    if not Path(filename).is_file():
        raise ValueError(f"The provided {filename} does not exist")
    with open(filename) as f:
        return json.load(f)


@task(task_run_name="{uid}-get-component-json")
def get_component_json(uid: str):
    logger = get_run_logger()
    component = get_component_by_uid(uid)
    logger.info("Extracting raw component details")
    return get_json_from_file(component.jsonfile)


# I could not use subprocess.run for both types of commands
# hence the need to use popen and run
def run_command(cmd: str, cmd_engine: str):
    if cmd_engine == "customerconnect":
        return subprocess.Popen(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
    else:
        try:
            status = subprocess.run(
                args=cmd,
                capture_output=True,
                shell=True,
                check=True,
            )
            return status
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

        # return subprocess.run(
        #     args=cmd,
        #     capture_output=True,
        #     shell=True,
        #     check=True,
        # )


def get_customerconnect_credentials() -> Tuple[str, str]:
    vcc_username = DBUtils.get_setting_value("zpodfactory_customerconnect_username")
    vcc_password = DBUtils.get_setting_value("zpodfactory_customerconnect_password")

    return vcc_username, vcc_password


def get_avi_pulse_releases(component):
    response = requests.get(component.component_url)
    major_versions = response.json().get("result").get("major_version")
    releases = [
        {
            "id": release.get("system_list")[0].get("id"),
            "name": release.get("major_name"),
        }
        for release in major_versions
    ]
    return releases


def get_avi_pulse_release_id(component):
    releases = get_avi_pulse_releases(component)
    for release in releases:
        if release.get("name") == component.component_version:
            return release.get("id")
    return None


def get_avi_pulse_files(component, release_id):
    url = f"{component.component_url}/{release_id}"
    response = requests.get(url, headers={"Accept": "application/json"})
    downloads = response.json().get("result").get("software_detail_list")
    release_files = [
        download.get("ecosystem_software_list")
        for download in downloads
        if download.get("ecosystem_name") == "VMware"
    ]
    return release_files[0]


def get_avi_pulse_file_id(avi_pulse_files):
    for file in avi_pulse_files:
        if "SHA1" not in file.get("software_name").split(" "):
            return file.get("software_id")


def get_avi_pulse_file_dowload_url(component, release_id, release_file_id):
    url = f"{component.component_url}/downloads/{release_id}/{release_file_id}"
    response = requests.get(url)
    return {
        "url": response.json().get("url"),
        "filename": response.json().get("filename"),
    }


def get_avi_pulse_file_download_cmd(component):
    release_id = get_avi_pulse_release_id(component)
    release_files = get_avi_pulse_files(component, release_id)
    release_file_id = get_avi_pulse_file_id(release_files)
    release_file_url = get_avi_pulse_file_dowload_url(
        component, release_id, release_file_id
    )
    return (
        "wget "
        "--no-check-certificate "
        f" {shlex.quote(release_file_url['url'])}"
        f" -O {shlex.quote(PRODUCTS_PATH)}/{shlex.quote(release_file_url['filename'])}"
        # f" -P {shlex.quote(PRODUCTS_PATH)}"
        f" -q"
    )


def generate_download_command(component: Component):
    print(
        "Generating download command for component:"
        f" {component.component_name}-{component.component_version}"
    )

    if component.component_download_engine == "https":
        return f"wget {shlex.quote(component.component_dl_url)} -P {shlex.quote(PRODUCTS_PATH)}"

    elif component.component_download_engine == "avipulse":
        try:
            return get_avi_pulse_file_download_cmd(component)
        except Exception as e:
            print("Failed to generate avipulse download command:", e)
            raise ValueError("Error generating avipulse download command")

    elif component.component_download_engine == "customerconnect":
        try:
            vcc_username, vcc_password = get_customerconnect_credentials()
            return (
                "vcc download"
                " -a"
                f" --user {shlex.quote(vcc_username)}"
                f" --pass {shlex.quote(vcc_password)}"
                f" -p {shlex.quote(component.component_download_product)}"
                f" -s {shlex.quote(component.component_download_subproduct)}"
                f" -v {shlex.quote(component.component_download_version)}"
                f" -f {shlex.quote(component.component_download_file)}"
                f" -o {shlex.quote(PRODUCTS_PATH)}"
                f" -t {shlex.quote(component.component_download_type)}"
                if component.component_download_type
                else ""
            )
        except Exception as e:
            print("Failed to retrieve customerconnect credentials:", e)
            raise ValueError("Error retrieving customerconnect credentials")

    else:
        raise ValueError(
            f"Unsupported download engine: {component.component_download_engine}"
        )


@task(
    task_run_name="{component.component_uid}-download",
)
def download_component(component: Component) -> int:
    logger = get_run_logger()
    https_cmd = (
        generate_download_command(component)
        if component.component_download_engine in ["https", "avipulse"]
        else ""
    )
    customer_connect_cmd = (
        generate_download_command(component)
        if component.component_download_engine == "customerconnect"
        else ""
    )
    cmd = (
        https_cmd
        if component.component_download_engine in {"https", "avipulse"}
        else customer_connect_cmd
    )

    hidden_pass_cmd = customer_connect_cmd = re.sub(
        r"(--pass\s+)(\S+)", r"\1" + "********", customer_connect_cmd
    )
    print_cmd = (
        https_cmd
        if component.component_download_engine in ["https", "avipulse"]
        else hidden_pass_cmd
    )
    print("Printing....", print_cmd)
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

        process = run_command(cmd=cmd, cmd_engine=component.component_download_engine)

        while (
            component.component_download_engine == "customerconnect"
            and process.poll() is None
        ):
            process.stdout.readline()

        return_code = (
            process.wait()
            if component.component_download_engine == "customerconnect"
            else process.returncode
        )
        if return_code != 0:
            msg = (
                process.stderr.read().decode().strip()
                if component.component_download_engine == "customerconnect"
                else process.stdout.decode()
            )
            logger.info(f"stderr: {msg}")
            if "Authentication failure" in msg:
                raise RuntimeError("AuthenticationError")
            if "You are not entitled" in msg:
                raise RuntimeError("EntitlementError")
        else:
            logger.info(f"{component.component_uid} downloaded")
            return 0
    except RuntimeError as e:
        if "AuthenticationError" in e.args:
            update_db(
                component.component_uid, ComponentDownloadStatus.FAILED_AUTHENTICATION
            )
            logger.error("The provided credentials are not valid.")
        if "EntitlementError" in e.args:
            update_db(
                component.component_uid, ComponentDownloadStatus.FAILED_NOT_ENTITLED
            )
            logger.error(
                "The provided credentials are not entitled to download this sub-product"
            )

        # We want Prefect task to fail !
        raise e

    except Exception as e:
        logger.error(f"Error downloading {component.component_uid}")
        update_db(component.component_uid, ComponentDownloadStatus.FAILED_UNKNOWN)
        logger.error(e)
        raise e


@task(task_run_name="{uid}-get-component")
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


def wait_for_file(file_path, retries=10, wait_time=5):
    for _ in range(retries):
        if os.path.exists(file_path):
            print(f"File found at {file_path}")
            return True
        else:
            print(
                f"File not found at {file_path}. Waiting for "
                f"{wait_time} seconds before retrying."
            )
            time.sleep(wait_time)
    print(f"File not found at {file_path} after {retries} retries.")
    return False


@task(task_run_name="{component.component_uid}-verify-checksum")
def verify_checksum(component: Component, filename: Path) -> bool:
    logger = get_run_logger()

    file_exists = wait_for_file(filename)
    if not file_exists:
        logger.info(f"The specified {filename} does not exist")
        raise ValueError(f"{filename} does not exist")

    if component.component_download_file_checksum is None:
        if component.component_dl_path.exists():
            update_db(component.component_uid, ComponentDownloadStatus.COMPLETED)
        return

    logger.info(f"Verifying {component.component_uid} checksum ...")
    checksum_str = component.component_download_file_checksum
    expected_checksum = checksum_str.split(":")[1]
    checksum = compute_checksum(component, filename)
    logger.info(f"File Checksum: {checksum}")
    if checksum != expected_checksum:
        logger.info(f"Expected Checksum: {expected_checksum}")
        update_db(component.component_uid, ComponentDownloadStatus.FAILED_CHECKSUM)
        raise ValueError("Checksum does not match")
    logger.info(f"Updating {component.component_uid} status")
    update_db(
        component.component_uid,
        ComponentDownloadStatus.COMPLETED,
        ComponentStatus.ACTIVE,
    )
    return True


def calculate_percentage(current_size, expected_size):
    return round(100 * current_size / expected_size)


def get_download_paths(component: Component) -> Tuple[str, str]:
    dl_path = component.component_dl_path
    tmp_dl_path = f"{dl_path}.tmp"
    return dl_path, tmp_dl_path


def track_download_progress(dl_path, tmp_dl_path, file_size, component, timeout=30):
    print("Download Path", dl_path)
    print(tmp_dl_path)
    logger = get_run_logger()
    start_time = time.time()
    # logger.info("Tracking dowloading process")
    while not Path(dl_path).exists() and not Path(tmp_dl_path).exists():
        elapsed_time = time.time() - start_time

        #  Stop tracking progress when download_status is:
        # - FAILED_AUTHENTICATION
        # - FAILED_NOT_ENTITLED
        #
        # Raise an error so Prefect engine fails the Task
        #
        c = get_component_by_uid(component.component_uid)

        if c.download_status in [
            ComponentDownloadStatus.FAILED_AUTHENTICATION,
            ComponentDownloadStatus.FAILED_NOT_ENTITLED,
        ]:
            raise RuntimeError(f"VMware Customer Connect error: {c.download_status} !")

        if elapsed_time > timeout:
            logger.info(f"Timeout, waiting for file to track { dl_path} {tmp_dl_path}")
            return "Timeout"

        time.sleep(1)

    file_path = dl_path if Path(dl_path).exists() else tmp_dl_path

    downloaded_size = Path(file_path).stat().st_size

    progress = calculate_percentage(downloaded_size, file_size)

    return f"{progress}" if progress < 100 else "DOWNLOAD_COMPLETED"


@task(task_run_name="{component.component_uid}-update-download-progress")
def update_download_progress(component):  # sourcery skip: raise-specific-error
    logger = get_run_logger()
    dl_path, tmp_dl_path = get_download_paths(component)
    expected_size = round(convert_to_byte(component=component))

    logger.info(f"Tracking download progress for component {component.component_uid}")

    while True:
        c = get_component_by_uid(component.component_uid)

        progress = track_download_progress(dl_path, tmp_dl_path, expected_size, c)

        if progress == "Timeout":
            logger.info("Timeout: no file to track, exiting")
            break

        update_db(component.component_uid, progress)
        logger.info(
            f"Download progress for component {component.component_uid}: {progress}%"
        )

        if progress == "DOWNLOAD_COMPLETED":
            logger.info(
                f"Download progress for component {component.component_uid}: 100%"
            )
            return True

        time.sleep(5)

    return False


@task(task_run_name="{component.component_uid}-dir-clean-up")
def clean_up_existing_files(component: Component):
    logger = get_run_logger()
    logger.info(f"Cleaning up existing files for {component.component_uid}")
    dst_dir = (
        Path(PRODUCTS_PATH) / component.component_name / component.component_version
    )
    if dst_dir.exists():
        logger.info(f"Removing {dst_dir}")
        shutil.rmtree(str(dst_dir), ignore_errors=True)
    logger.info(f"Finished cleaning up existing files for {component.component_uid}")


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


@flow(
    name="component_download",
    log_prints=True,
    flow_run_name="{uid}-download",
)
def flow_component_download(uid: str):
    logger = get_run_logger()
    request = get_component_json(uid=uid)
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

    clean_up_existing_files(component=component)

    logger.info(f"No {uid} found, will proceed to download the component")
    download_component.submit(component=component)

    status_task = update_download_progress.submit(component=component)
    result = status_task.result()

    logger.info(f"update_download_progress Status: {result}")

    # tsugliani:
    # Adding this because something is not working in this whole logic again :-(
    c = get_component_by_uid(component.component_uid)
    if c.download_status in [
        ComponentDownloadStatus.FAILED_AUTHENTICATION,
        ComponentDownloadStatus.FAILED_NOT_ENTITLED,
    ]:
        raise RuntimeError(
            "VMware Customer Connect error: Check Account entitlements/credentials !"
        )

    if not result:
        update_db(component.component_uid, ComponentDownloadStatus.FAILED_UNKNOWN)
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
    flow_component_download()
