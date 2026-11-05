"""SSH into a test zPod's VMs with the factory's key, to check what really changed.

The API answering "ACTIVE" proves a database row; these helpers prove the
VLAN interface, the nftables rule, the mount or the export is really there.

Every zPod VM deployed by zPodFactory gets the public key stored in the
`zpodfactory_ssh_key` setting (OVF/extraConfig `zpod_sshkey`). The suite logs
in with the matching private key (`E2E_ZPOD_SSH_KEY`) and `BatchMode=yes`: no
password prompt can rescue a broken key injection, so a working login is
itself a test of the deploy.

VMs that are only reachable inside the zPod (on a user VLAN) are reached
through zcore as a jump host, with the same key.
"""

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

SSH_BASE_OPTS = [
    "-o", "BatchMode=yes",
    "-o", "IdentitiesOnly=yes",
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "LogLevel=ERROR",
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=15",
]


class SshCommandError(Exception):
    def __init__(self, target: str, command: str, returncode: int, stdout: str, stderr: str):
        self.target = target
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"ssh {target} `{command}` exited {returncode}\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
        )


@dataclass
class SshResult:
    target: str
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class ZpodSsh:
    """One SSH target (zcore, or a VM behind it) logged into with the factory key.

        zc = zpod_ssh(zpod_name)                  # zcore of that zPod
        zc("ip -br addr show")                    # SshResult, raises on non-zero
        zc.jump("10.42.111.50")("hostname")        # a VM inside the zPod, via zcore
    """

    host: str
    key_path: Path
    user: str = "root"
    jump_host: str | None = None
    jump_user: str = "root"

    @property
    def target(self) -> str:
        via = f" via {self.jump_user}@{self.jump_host}" if self.jump_host else ""
        return f"{self.user}@{self.host}{via}"

    def _argv(self, command: str) -> list[str]:
        argv = ["ssh", *SSH_BASE_OPTS, "-i", str(self.key_path)]
        if self.jump_host:
            proxy = " ".join(
                ["ssh", *SSH_BASE_OPTS, "-i", shlex.quote(str(self.key_path)), "-W", "%h:%p",
                 f"{self.jump_user}@{self.jump_host}"]
            )
            argv += ["-o", f"ProxyCommand={proxy}"]
        argv += [f"{self.user}@{self.host}", command]
        return argv

    def __call__(self, command: str, *, check: bool = True, timeout: int = 60) -> SshResult:
        start = time.monotonic()
        try:
            proc = subprocess.run(self._argv(command), capture_output=True, text=True, timeout=timeout)
            returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            returncode = 124
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = f"timed out after {timeout}s"
        duration = time.monotonic() - start

        try:
            from e2e.report import recorder

            recorder.log_ssh(self.target, command, returncode, stdout or stderr, duration)
        except Exception:
            pass  # reporting must never break a test

        if check and returncode != 0:
            raise SshCommandError(self.target, command, returncode, stdout, stderr)
        return SshResult(self.target, command, returncode, stdout, stderr)

    def jump(self, host: str, user: str = "root") -> ZpodSsh:
        """A VM inside this zPod, reached through this host."""
        return ZpodSsh(host=host, key_path=self.key_path, user=user, jump_host=self.host, jump_user=self.user)

    def wait_ready(self, *, timeout_seconds: int = 300, interval_seconds: int = 10) -> None:
        """Wait until key-based login works (a fresh VM can be ACTIVE before sshd is up)."""
        deadline = time.monotonic() + timeout_seconds
        last = None
        while time.monotonic() < deadline:
            last = self("true", check=False, timeout=20)
            if last.ok:
                return
            time.sleep(interval_seconds)
        raise SshCommandError(self.target, "true", last.returncode if last else -1,
                              last.stdout if last else "", last.stderr if last else "no attempt")


def public_key_of(key_path: Path) -> str:
    """The `<type> <base64>` part of the private key's public half (comment dropped)."""
    pub = Path(f"{key_path}.pub")
    if pub.is_file():
        text = pub.read_text()
    else:
        text = subprocess.run(
            ["ssh-keygen", "-y", "-f", str(key_path)], capture_output=True, text=True, check=True
        ).stdout
    return " ".join(text.split()[:2])
