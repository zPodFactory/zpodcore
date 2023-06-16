#!/usr/bin/env python3
import subprocess
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class Handler(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return None
        print(f"{event.src_path} file was {event.event_type}")
        if event.event_type in ("modified"):
            print(
                f"{event.src_path} file was {event.event_type} - "
                "Send SIGHUP to dnsmasq..."
            )
            subprocess.call(["pkill", "-SIGHUP", "dnsmasq"])


if __name__ == "__main__":
    event_handler = Handler(patterns=["servers.conf"])
    observer = Observer()
    observer.schedule(
        event_handler,
        "/zPod/zPodDnsServers",
        recursive=False,
    )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
