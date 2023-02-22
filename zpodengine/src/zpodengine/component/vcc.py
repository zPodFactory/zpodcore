import hashlib
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, Union

# from prefect import get_run_logger
from pydantic import BaseModel
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskID, TimeElapsedColumn

# logger = get_run_logger()

progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn(),
)


class ComponentDownload(BaseModel):
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


class DownloadStatus(BaseModel):
    status: str


class DownloadHelper:
    byte_size = 1024
    powers = {"KB": 1, "MB": 2, "GB": 3, "TB": 4, "PB": 5}

    def __init__(
        self,
        vcc_username,
        vcc_password,
        zpod_path,
        component_download: ComponentDownload,
    ):
        self.component_download = component_download
        self.download_username = vcc_username
        self.download_password = vcc_password
        self.zpod_files_path = zpod_path
        self.file_path = Path(
            f"{self.zpod_files_path}/{self.component_download.component_download_file}"
        )
        self.file_path_tmp = Path(
            (
                f"{self.zpod_files_path}/"
                f"{self.component_download.component_download_file}.tmp"
            )
        )
        self.dst_file_dir = Path(
            (
                f"{self.zpod_files_path}/{self.component_download.component_name}"
                f"/{self.component_download.component_version}"
            )
        )
        self.dst_file = Path(
            f"{self.dst_file_dir}/{self.component_download.component_download_file}"
        )
        self.console = Console()

    def convert_to_byte(self) -> int:
        size, unit = self.get_size_unit()
        return int(size * (self.byte_size ** self.powers[unit]))

    def get_size_unit(self) -> Tuple[float, str]:
        size_str, unit_str = self.component_download.component_download_file_size.split(
            " "
        )
        size = float(size_str)
        unit = unit_str.upper()
        return size, unit

    @staticmethod
    def compute_checksum(checksum_engine: str, filename: Path) -> str:
        with open(filename, "rb") as f:
            bytes_read = f.read()
            if checksum_engine == "md5":
                return hashlib.md5(bytes_read).hexdigest()
            if checksum_engine == "sha256":
                return hashlib.sha256(bytes_read).hexdigest()
            if checksum_engine == "sha1":
                return hashlib.sha1(bytes_read).hexdigest()

    def verify_checksum(self, filename: Path) -> bool:
        print(
            "Verifying checksum for {self.component_download.component_download_file}"
        )
        checksum_engine, expected_checksum = self.get_checksum_details()
        checksum = self.compute_checksum(checksum_engine, filename)
        if checksum == expected_checksum:
            print("Successfully verified the checksume")
            return True

    def get_checksum_details(self) -> Tuple[str, str]:
        checksum_str = self.component_download.component_download_file_checksum
        checksum_engine, expected_checksum = checksum_str.split(":")
        return checksum_engine, expected_checksum

    @staticmethod
    def is_file_exists(filename: Path):
        try:
            return filename.exists()
        except FileNotFoundError as e:
            print(f"Cannot locate {e}")
            return False

    def get_download_status(self) -> DownloadStatus:
        expected_size = round(self.convert_to_byte())
        current_size = self.get_file_size(self.file_path, self.file_path_tmp)
        status = self.get_status(self.dst_file, current_size, expected_size)
        return DownloadStatus(status=status)

    @staticmethod
    def get_file_size(file_path: Path, tmp_file_path: Path) -> Union[int, None]:
        if file_path.is_file():
            return file_path.stat().st_size
        elif tmp_file_path.is_file():
            return tmp_file_path.stat().st_size
        return None

    @staticmethod
    def check_percentage(current_size, expected_size):
        return round((100 * current_size / expected_size))

    def get_status(
        self, dst_file: Path, current_size: Union[int, None], expected_size: int
    ) -> str:
        if dst_file.is_file():
            return "DOWNLOAD_COMPLETE"
        elif current_size is not None:
            return str(self.check_percentage(current_size, expected_size))
        return "SCHEDULED"

    def rename_file(self):
        print(
            f"Moving {self.component_download.component_download_file} to its final destination"
        )
        self.dst_file_dir.mkdir(parents=True, mode=0o775, exist_ok=True)
        self.file_path.rename(self.dst_file)
        if self.dst_file.exists():
            print(f"{self.component_download.component_download_file} renamed")

    def show_progress(self, task_id: TaskID, status: dict):
        if self.dst_file.exists():
            print(
                f"{self.component_download.component_download_file} is done downloading"
            )
            return
        if not self.file_path_tmp.is_file() and self.file_path.is_file():
            return

        expected_size = round(self.convert_to_byte())
        while True:
            current_size = (
                self.file_path.stat().st_size
                if self.file_path.exists()
                else self.file_path_tmp.stat().st_size
            )
            pct = round((100 * current_size / expected_size))
            if pct == 100:
                break
            status[task_id] = {"status": pct, "total": 100}
            time.sleep(0.1)
        return True

    def download_component(self):
        cmd = (
            f"vcc download -a --user {shlex.quote(self.download_username)}"
            f" --pass {shlex.quote(self.download_password)}"
            f" -p {shlex.quote(self.component_download.component_download_product)}"
            f" -s {shlex.quote(self.component_download.component_download_subproduct)}"
            f" -v {shlex.quote(self.component_download.component_version)}"
            f" -f {shlex.quote(self.component_download.component_download_file)}"
            f" -o {shlex.quote(self.zpod_files_path)}"
        )

        try:
            vcc = subprocess.run(
                args=cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=True,
            )
            print(f"{vcc.stdout.decode()}")
            print(f"{vcc.stderr.decode()}")
            return self.file_path

        except subprocess.CalledProcessError as e:
            print(
                f"Error downloading {self.component_download.component_download_file}"
            )
            print(e)

    def verify_if_component_exists(self):
        print(f"Checking if we have {self.component_download.component_download_file}")
        file_exists = False
        if self.is_file_exists(self.dst_file):
            self.verify_checksum(self.dst_file)
            file_exists = True
        elif self.is_file_exists(self.file_path):
            self.verify_checksum(self.file_path)
            self.rename_file()
            file_exists = True
        if file_exists:
            print(f"{self.component_download.component_download_file} already exists")
        return file_exists
