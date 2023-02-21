from prefect import flow, task

from . import vcc


@task()
def get_component(filename: str, filepath: str):
    return vcc.read_json_file(filename, filepath)


@task()
def is_component_exists(download_helper: vcc.DownloadHelper) -> bool:
    if download_helper.verify_if_component_exists():
        return True


@task()
def move_component(download_helper: vcc.DownloadHelper):
    download_helper.rename_file()


@task()
def download_file(download_helper: vcc.DownloadHelper):
    file = download_helper.download_component()
    if download_helper.is_file_exists(file):
        download_helper.rename_file()


@flow(log_prints=True, name="download")
def component_download(
    vcc_username: str, vcc_password: str, filename: str, filepath: str, zpod_path: str
):
    request = get_component(filename=filename, filepath=filepath)
    download_helper = vcc.DownloadHelper(
        vcc_username=vcc_username,
        vcc_password=vcc_password,
        zpod_path=zpod_path,
        component_download=vcc.ComponentDownload(**request),
    )
    if is_component_exists(download_helper):
        return
    else:
        download_file(download_helper)


if __name__ == "__main__":
    component_download()
