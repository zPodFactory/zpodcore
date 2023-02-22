
from prefect import flow, get_run_logger, task

from . import vcc


@task(task_run_name="validating-{component_download_file}-request")
def validate_request(vcc_request, component_download_file):
    print(f"Validating request to download {component_download_file}")
    logger = get_run_logger()
    try:
        return vcc.ComponentDownload(**vcc_request)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")


@task(task_run_name="check-if-{component_download_file}-exists")
def is_exists(download_helper: vcc.DownloadHelper, component_download_file) -> bool:
    print(f"Let's check if {component_download_file} file already exists or not")
    return download_helper.verify_if_component_exists()


@task(task_run_name="download-{component_download_file}")
def download_file(download_helper: vcc.DownloadHelper, component_download_file):
    print(f"Intiating {component_download_file} download. Standby")
    return download_helper.download_component()


# @flow(
#     flow_run_name="check-if-{download_helper.component_download.component_download_file}-exist"
# )
# def verify_component_exists(download_helper: vcc.DownloadHelper):
#     return is_exists(download_helper=download_helper)


@flow(flow_run_name="verify-{component_download_file}-request")
def verify_component_request(vcc_request, component_download_file):
    print(f"Verifying sanity of the download request {component_download_file}")
    return validate_request(vcc_request, component_download_file)


# @flow()
# def rename_component(file: Path, download_helper: vcc.DownloadHelper):
#     if download_helper.is_file_exists(file):
#         download_helper.rename_file()


@flow(name="download-component", log_prints=True)
def download_component(
    vcc_username: str,
    vcc_password: str,
    zpod_path: str,
    vcc_request: dict,
    component_download_file: str,
):
    print(f"Downloading {component_download_file}")
    component_download = verify_component_request(vcc_request, component_download_file)
    download_helper = vcc.DownloadHelper(
        vcc_username=vcc_username,
        vcc_password=vcc_password,
        zpod_path=zpod_path,
        component_download=component_download,
    )
    # if verify_component_exists(download_helper=download_helper):
    #     return
    if is_exists(
        download_helper=download_helper, component_download_file=component_download_file
    ):
        print(f"{component_download_file} exists. Nothing do.")
        return
    else:
        print(f"No records found for {component_download_file}")
        downloaded_file = download_file(
            download_helper=download_helper,
            component_download_file=component_download_file,
        )
    if download_helper.is_file_exists(downloaded_file):
        download_helper.rename_file()


if __name__ == "__main__":
    download_component()
