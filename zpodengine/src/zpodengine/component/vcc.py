import json
import time
import os
import sys
import shlex
import hashlib
import subprocess
from pathlib import Path
from pydantic import BaseModel
from rich.console import Console
from typing import Optional, Tuple, Union
from loguru import logger
from rich.progress import (
    BarColumn,
    Progress,
    TimeElapsedColumn,
    TaskID
)

log_file_dir = Path('/logs')
log_file = "/logs/component_downloads.log"
log_file_dir.mkdir(parents=True, mode=0o775, exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="<red>{time}</red> | <green>{level}</green> | {message}", colorize=True)
logger.add(log_file, rotation="30 MB", compression="zip")

progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn()
)


def read_json_file(filename: str, filepath: str):
    for subdir, _, files in os.walk(filepath):
        for file in files:
            if file == filename:
                full_file_path = os.path.join(subdir, file)
                with open(full_file_path) as f:
                    return json.load(f)


class ComponentDownload(BaseModel):
    component_name: str
    component_version: str
    component_type: Optional[str]
    component_description: Optional[str]
    component_url: Optional[str]
    component_download_engine: Optional[str]
    component_download_product: Optional[str]
    component_download_subproduct: Optional[str]
    component_download_version: Optional[str]
    component_download_file: Optional[str]
    component_download_file_checksum: Optional[str]  #
    component_download_file_size: Optional[str]
    component_isnested: Optional[bool]


class DownloadStatus(BaseModel):
    status: str


class DownloadHelper:
    byte_size = 1024
    powers = {
        "KB": 1,
        "MB": 2,
        "GB": 3,
        "TB": 4,
        "PB": 5
    }

    def __init__(self, vcc_username, vcc_password, zpod_path, component_download: ComponentDownload):
        self.component_download = component_download
        self.download_username = vcc_username
        self.download_password = vcc_password
        self.zpod_files_path = zpod_path
        self.file_path = Path(f"{self.zpod_files_path}/{self.component_download.component_download_file}")
        self.file_path_tmp = Path(f"{self.zpod_files_path}/{self.component_download.component_download_file}.tmp")
        self.dst_file_dir = Path(
            f"{self.zpod_files_path}/{self.component_download.component_name}/{self.component_download.component_version}"
        )
        self.dst_file = Path(f"{self.dst_file_dir}/{self.component_download.component_download_file}")
        self.console = Console()

    def convert_to_byte(self) -> int:
        size, unit = self.get_size_unit()
        return int(size * (self.byte_size ** self.powers[unit]))

    def get_size_unit(self) -> Tuple[float, str]:
        size_str, unit_str = self.component_download.component_download_file_size.split(" ")
        size = float(size_str)
        unit = unit_str.upper()
        return size, unit

    def verify_checksum(self) -> bool:
        checksum_engine, expected_checksum = self.get_checksum_details()
        checksum = self.compute_checksum(checksum_engine)
        if checksum == expected_checksum:
            return True
        return False

    def get_checksum_details(self) -> Tuple[str, str]:
        checksum_str = self.component_download.component_download_file_checksum
        checksum_engine, expected_checksum = checksum_str.split(":")
        return checksum_engine, expected_checksum

    def compute_checksum(self, checksum_engine: str) -> str:
        with open(self.file_path, "rb") as f:
            bytes_read = f.read()
            if checksum_engine == "md5":
                return hashlib.md5(bytes_read).hexdigest()
            if checksum_engine == "sha256":
                return hashlib.sha256(bytes_read).hexdigest()
            if checksum_engine == "sha1":
                return hashlib.sha1(bytes_read).hexdigest()

    @staticmethod
    def is_file_exists(filename: Path):
        return filename.exists()

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

    def get_status(self, dst_file: Path, current_size: Union[int, None], expected_size: int) -> str:
        if dst_file.is_file():
            return "DOWNLOAD_COMPLETE"
        elif current_size is not None:
            return str(self.check_percentage(current_size, expected_size))
        return "SCHEDULED"

    def rename_file(self):
        self.dst_file_dir.mkdir(parents=True, mode=0o775, exist_ok=True)
        self.file_path.rename(self.dst_file)
        if self.dst_file.exists():
            logger.info(f"File {self.component_download.component_download_file} renamed successfully")

    def show_progress(self, task_id: TaskID, status: dict):
        if self.dst_file.exists():
            logger.info(f"{self.component_download.component_download_file} is done downloading")
            return
        if not self.file_path_tmp.is_file() and self.file_path.is_file():
            return

        expected_size = round(self.convert_to_byte())
        while True:
            current_size = self.file_path.stat().st_size if self.file_path.exists() else self.file_path_tmp.stat().st_size
            pct = round((100 * current_size / expected_size))
            if pct == 100:
                break
            status[task_id] = {
                "status": pct,
                "total": 100
            }
            time.sleep(0.1)
        return True

    def download_component(self):
        logs = Path(f"{self.zpod_files_path}/logs")
        logs.mkdir(parents=True, mode=0o775, exist_ok=True)

        cmd = (
            f"/usr/local/bin/vcc download -a --user {shlex.quote(self.download_username)}"
            f" --pass {shlex.quote(self.download_password)}"
            f" -p {shlex.quote(self.component_download.component_download_product)}"
            f" -s {shlex.quote(self.component_download.component_download_subproduct)}"
            f" -v {shlex.quote(self.component_download.component_version)}"
            f" -f {shlex.quote(self.component_download.component_download_file)}"
            f" -o {shlex.quote(self.zpod_files_path)}"
        )

        try:
            vcc = subprocess.run(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
            logger.info(f"{vcc.stdout.decode()}")
            logger.error(f"{vcc.stderr.decode()}")

            if self.is_file_exists(self.file_path):
                logger.info(f"{self.component_download.component_download_file} downloaded")
                logger.info(f"Verifying checksum for {self.component_download.component_download_file}")
                if self.verify_checksum():
                    logger.info(f"Checksum verified")
                self.rename_file()

        except subprocess.CalledProcessError as e:
            logger.error(e)
            logger.error(f"Unable to download {self.component_download.component_download_file}")

    def verify_if_component_exists(self):
        if self.is_file_exists(self.file_path):
            if self.verify_checksum():
                logger.info(f"{self.component_download.component_download_file} already exists")
                return True
        return False

    def download_file(self) -> None:
        if self.is_file_exists(self.dst_file):
            logger.info(f"{self.component_download.component_download_file} already exists")
            return
        self.download_component()