import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union

from prefect import flow, get_run_logger, task
from prefect.task_runners import SequentialTaskRunner
from pydantic import BaseModel

from zpodengine import settings

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
    component_download_product: str
    component_download_subproduct: Optional[str]
    component_download_version: str
    component_download_file: str
    component_download_file_checksum: str  # "sha265:checksum"
    component_download_file_size: str
    component_isnested: Optional[bool]
    component_dst_path: Path | None = None
    component_dl_path: Path | None = None


@task(retries=3, retry_delay_seconds=30)
def download_component(component: Component):
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
    wget_cmd = "wget" f"{component.component_download_file}" "-P" f"{PRODUCTS_PATH}"

    cmd = wget_cmd if component.component_download_engine == "https" else cc_cmd

    try:
        vcc = subprocess.run(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            check=True,
        )
        # print(f"{vcc.stdout.decode()}")
        # print(f"{vcc.stderr.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {component.component_download_file}")
        print(e)

    if vcc.returncode != 0:
        raise ValueError("Incomplete download")


def get_libraries():
    libraries = []
    for subdir, _, files in os.walk(LIBRARY_PATH):
        libraries.extend(
            os.path.join(subdir, filename)
            for filename in files
            if filename.endswith(".json")
        )
    library_contents = []
    for libary in libraries:
        with open(libary) as f:
            library_contents.append(json.load(f))
    return library_contents


@task(log_prints=True)
def get_component(component_uid: str):
    logger = get_run_logger()
    # TODO: confirm that component_uid will be consitent. Right now spliting on hyphen
    libraries = get_libraries()
    logger.info("Wait while we get component details")
    compnent_name, component_version = component_uid.split("-")
    try:
        raw_component = [
            library
            for library in libraries
            if library["component_name"] == compnent_name
            and library["component_version"] == component_version
        ][0]
        logger.info("Component details found")
    except ImportError as e:
        logger.info("Cannot locate library associated with this request")
        logger.error(e)
        return None

    logger.info("Validating component...")
    component = Component(**raw_component)
    dst_dir = (
        Path(PRODUCTS_PATH) / component.component_name / component.component_version
    )
    component.component_dst_path = Path(dst_dir) / component.component_download_file
    component.component_dl_path = (
        Path(PRODUCTS_PATH) / component.component_download_file
    )
    logger.info("Component validated successfully")
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
    logger.info("In compute function")
    checksum_str = component.component_download_file_checksum
    checksum_engine = checksum_str.split(":")[0]
    with open(filename, "rb") as f:
        bytes_read = f.read()
        return getattr(hashlib, checksum_engine)(bytes_read).hexdigest()


def is_file_exists(filename: Path) -> bool:
    try:
        return filename.exists()
    except FileNotFoundError as e:
        print(f"Cannot locate {e}")
        return False


@task
def verify_checksum(component: Component, filename: Path) -> bool:
    print(f"Verifying checksum for {component.component_download_file}")
    checksum_str = component.component_download_file_checksum
    expected_checksum = checksum_str.split(":")[1]
    checksum = compute_checksum(component, filename)
    if checksum != expected_checksum:
        raise ValueError("Checksum does not match")


def get_download_status(component: Component) -> ComponentStatus:
    status = "SCHEDULED"
    expected_size = round(convert_to_byte(component=component))
    current_size = get_file_size(component)
    if component.component_dst_path.is_file():
        status = "DOWNLOAD_COMPLETE"
    if current_size is not None:
        status = str(check_percentage(current_size, expected_size))
    return ComponentStatus(
        component_name=component.component_name,
        component_version=component.component_version,
        component_status=status,
    )


def check_percentage(current_size, expected_size):
    return round((100 * current_size / expected_size))


@task()
def rename_file(component: Component):
    print(f"Moving {component.component_download_file} to its final destination")
    dst_dir = (
        Path(PRODUCTS_PATH) / component.component_name / component.component_version
    )

    dst_dir.mkdir(parents=True, mode=0o775, exist_ok=True)
    print(dst_dir)
    component.component_dl_path.rename(component.component_dst_path)
    if component.component_dst_path.exists():
        print(f"{component.component_download_file} renamed")


@task()
def check_if_component_exist(component: Component):
    print(f"Checking if we have {component.component_download_file}")
    if is_file_exists(component.component_dst_path):
        return verify_checksum(component, component.component_dst_path)
    if is_file_exists(component.component_dl_path):
        return verify_checksum(component, component.component_dl_path)
    return False


@flow(log_prints=True, task_runner=SequentialTaskRunner)
def download_component_flow(component_uid: str):
    component = get_component(component_uid=component_uid)

    if (
        component.component_dst_path.is_file()
        and verify_checksum(
            component,
            component.component_dst_path,
            return_state=True,
        ).is_completed()
    ):
        print(f"{component.component_download_file} already exists. Nothing to do")
        return

    download_component(component)
    get_download_status

    if not verify_checksum(
        component=component,
        filename=component.component_dl_path,
        return_state=True,
    ).is_completed():
        # Restart flow
        pass
    rename_file(component=component)


if __name__ == "__main__":
    download_component_flow()
