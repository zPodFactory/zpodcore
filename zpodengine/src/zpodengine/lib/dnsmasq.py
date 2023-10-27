import fcntl
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def lock_file(file):
    pfile = Path(file)
    if not pfile.is_file():
        pfile.write_text("")

    while True:
        try:
            file_handle = pfile.open("r+")
            fcntl.flock(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except IOError:  # noqa: UP024
            # File is locked, wait for a while and try again
            time.sleep(0.1)

    try:
        yield file_handle
    finally:
        fcntl.flock(file_handle, fcntl.LOCK_UN)
        file_handle.close()


def add(instance_domain, ip):
    print(f"Adding dnsmasq record for: {instance_domain}, {ip}")
    with lock_file("/zpod/dnsmasq_servers/servers.conf") as f:
        lines = set(f.readlines())
        lines.add(f"server=/{instance_domain}/{ip}\n")
        write(f, lines)


def delete(instance_name):
    print(f"Deleting dnsmasq record for: {instance_name}")
    lookfor = f"server=/{instance_name}."
    with lock_file("/zpod/dnsmasq_servers/servers.conf") as f:
        lines = {x for x in f.readlines() if not x.startswith(lookfor)}
        write(f, lines)


def write(f, lines: set):
    f.seek(0)
    f.truncate()
    f.writelines(sorted(lines))
