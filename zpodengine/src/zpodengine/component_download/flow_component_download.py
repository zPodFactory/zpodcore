import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

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

# Component JSONs may store the Broadcom depot URL with a ${BROADCOM_DOWNLOAD_TOKEN}
# placeholder; it is substituted with the zpodfactory_broadcom_download_token
# setting at download time, so the per-customer token stays out of library files.
BROADCOM_TOKEN_PLACEHOLDER = "${BROADCOM_DOWNLOAD_TOKEN}"
_BROADCOM_URL_TOKEN_RE = re.compile(r"(https://dl\.broadcom\.com/)[^/]+(/PROD/)")


def _resolve_broadcom_token(url: str) -> str:
    """Substitute the Broadcom token placeholder with the configured value."""
    if BROADCOM_TOKEN_PLACEHOLDER not in url:
        return url
    token = DBUtils.get_setting_value("zpodfactory_broadcom_download_token")
    if not token:
        raise ValueError(
            "Broadcom depot URL uses ${BROADCOM_DOWNLOAD_TOKEN} but the "
            "zpodfactory_broadcom_download_token setting is not set."
        )
    return url.replace(BROADCOM_TOKEN_PLACEHOLDER, token)


def _redact_broadcom_token(s: str) -> str:
    """Mask the token in a Broadcom depot URL for safe logging."""
    return _BROADCOM_URL_TOKEN_RE.sub(r"\1***\2", s)


class Component(BaseModel):
    component_name: str
    component_version: str
    component_type: str | None = None
    component_description: str | None = None
    component_download_engine: str
    component_download_file: str | None = None
    component_download_file_checksum: str | None = None  # "sha265:checksum"
    component_download_file_size: str
    component_isnested: bool | None = None
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


class UnsupportedEngineError(ValueError):
    """The library component declares a download engine we no longer support."""


def generate_download_command(component: Component):
    print(
        "Generating download command for component:"
        f" {component.component_name}-{component.component_version}"
    )

    if component.component_download_engine == "https":
        return (
            f"wget {shlex.quote(component.component_dl_url)}"
            f" -P {shlex.quote(PRODUCTS_PATH)}"
        )

    raise UnsupportedEngineError(
        f"Unsupported download engine: "
        f"{component.component_download_engine!r}. Only 'https' is "
        f"supported; the library component needs to be updated."
    )


@task(
    task_run_name="{component.component_uid}-download",
)
def download_component(component: Component) -> int:
    logger = get_run_logger()
    prev_download = Path(PRODUCTS_PATH) / component.component_download_file

    try:
        # Inside the try so UnsupportedEngineError is caught and the
        # FAILED_UNSUPPORTED_ENGINE status gets written to the DB.
        cmd = generate_download_command(component)

        if prev_download.exists():
            logger.info(
                f"Cleaning previously failed {component.component_uid} download"
            )
            os.remove(prev_download)

        logger.info(
            f"Downloading {component.component_name}-{component.component_version} ..."
        )
        logger.info(f"Executing download command {_redact_broadcom_token(cmd)}")

        subprocess.run(args=cmd, capture_output=True, shell=True, check=True)
        logger.info(f"{component.component_uid} downloaded")
        return 0
    except UnsupportedEngineError as e:
        logger.error(str(e))
        update_db(
            component.component_uid,
            ComponentDownloadStatus.FAILED_UNSUPPORTED_ENGINE,
        )
        raise e
    except subprocess.CalledProcessError as e:
        # wget surfaces HTTP errors on stderr. The Broadcom depot embeds the
        # token in the URL path, so a bad/expired token returns 403 Forbidden
        # (a missing one returns 401 Unauthorized) — both are auth failures
        # from the operator's point of view: the token needs updating.
        stderr = (e.stderr or b"").decode(errors="replace")
        if any(s in stderr for s in ("401", "403", "Unauthorized", "Forbidden")):
            logger.error(
                "Broadcom rejected the download (401/403) — the "
                "zpodfactory_broadcom_download_token setting is missing, "
                "invalid or expired; update it via the settings API."
            )
            update_db(
                component.component_uid,
                ComponentDownloadStatus.FAILED_AUTHENTICATION,
            )
        else:
            logger.error(
                f"Error downloading {component.component_uid}: {stderr or e}"
            )
            update_db(
                component.component_uid, ComponentDownloadStatus.FAILED_UNKNOWN
            )
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
        component.component_dl_url = _resolve_broadcom_token(
            component.component_download_file
        )
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


def get_file_size(component: Component) -> int | None:
    tmp_dl_path = f"{component.component_dl_path}.tmp"
    if component.component_dl_path.is_file():
        return component.component_dl_path.stat().st_size
    elif tmp_dl_path.is_file():
        return tmp_dl_path.stat().st_size
    return None


def get_size_unit(component: Component) -> tuple[float, str]:
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

    # Set download status to VERIFYING_CHECKSUM, as this takes a while for large OVAs.
    update_db(component.component_uid, ComponentDownloadStatus.VERIFYING_CHECKSUM)

    checksum_str = component.component_download_file_checksum
    expected_checksum = checksum_str.split(":")[1]
    checksum = compute_checksum(component, filename)
    logger.info(f"File Checksum: {checksum}")
    if checksum != expected_checksum:
        logger.info(f"Expected Checksum: {expected_checksum}")
        update_db(component.component_uid, ComponentDownloadStatus.FAILED_CHECKSUM)
        # Remove the bad file so the next download attempt starts clean and
        # we don't leave a checksum-mismatched payload at the staging path.
        try:
            Path(filename).unlink(missing_ok=True)
            logger.info(f"Removed {filename} (checksum mismatch)")
        except OSError as exc:
            logger.warning(f"Could not remove {filename}: {exc}")
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


def get_download_paths(component: Component) -> tuple[str, str]:
    dl_path = component.component_dl_path
    tmp_dl_path = f"{dl_path}.tmp"
    return dl_path, tmp_dl_path


def track_download_progress(dl_path, tmp_dl_path, file_size, timeout=30):
    logger = get_run_logger()
    start_time = time.time()
    while not Path(dl_path).exists() and not Path(tmp_dl_path).exists():
        elapsed_time = time.time() - start_time

        if elapsed_time > timeout:
            logger.info(f"Timeout, waiting for file to track {dl_path} {tmp_dl_path}")
            return "Timeout"

        time.sleep(1)

    file_path = dl_path if Path(dl_path).exists() else tmp_dl_path

    downloaded_size = Path(file_path).stat().st_size

    progress = calculate_percentage(downloaded_size, file_size)

    return (
        f"{progress}" if progress < 100 else ComponentDownloadStatus.DOWNLOAD_COMPLETED
    )


# component_download_file_size only drives the rendered percentage; if it is
# slightly off (rounding, eyeballed value, etc.) the percent can plateau just
# below 100 forever. Treat the download as finished once the file has stopped
# growing — checksum verify is the real correctness gate.
PROGRESS_POLL_SECONDS = 5
PROGRESS_STABLE_POLLS_DONE = 6  # 6 * 5s = 30s of unchanged file size


@task(task_run_name="{component.component_uid}-update-download-progress")
def update_download_progress(component):
    logger = get_run_logger()
    dl_path, tmp_dl_path = get_download_paths(component)
    expected_size = round(convert_to_byte(component=component))

    logger.info(f"Tracking download progress for component {component.component_uid}")

    last_size = -1
    stable_polls = 0

    while True:
        progress = track_download_progress(dl_path, tmp_dl_path, expected_size)

        if progress == "Timeout":
            logger.info("Timeout: no file to track, exiting")
            break

        update_db(component.component_uid, progress)
        logger.info(
            f"Download progress for component {component.component_uid}: {progress}%"
        )

        if progress == ComponentDownloadStatus.DOWNLOAD_COMPLETED:
            logger.info(
                f"Download progress for component {component.component_uid}: 100%"
            )
            return True

        # Permissive fallback: if the file has stopped growing for a while the
        # download is finished even if percent didn't quite reach 100.
        current_path = Path(dl_path) if Path(dl_path).exists() else Path(tmp_dl_path)
        current_size = (
            current_path.stat().st_size if current_path.exists() else -1
        )
        if current_size > 0 and current_size == last_size:
            stable_polls += 1
            if stable_polls >= PROGRESS_STABLE_POLLS_DONE:
                logger.info(
                    f"Download size stable at {current_size} bytes for "
                    f"{PROGRESS_STABLE_POLLS_DONE * PROGRESS_POLL_SECONDS}s; "
                    f"treating as completed (checksum verify will confirm)."
                )
                return True
        else:
            stable_polls = 0
        last_size = current_size

        time.sleep(PROGRESS_POLL_SECONDS)

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

    if not result:
        # Preserve any specific FAILED_* status that download_component
        # already set (auth, unsupported engine, etc.); only fall back to
        # FAILED_UNKNOWN when nothing more specific is on record.
        c = get_component_by_uid(component.component_uid)
        if not (c and str(c.download_status).startswith("FAILED_")):
            update_db(
                component.component_uid, ComponentDownloadStatus.FAILED_UNKNOWN
            )
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
