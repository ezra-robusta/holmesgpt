import hashlib
import logging
import os
import signal
import threading
import time
from typing import Callable, Optional

import yaml

from holmes.common.env_vars import ROBUSTA_CONFIG_PATH

POLL_INTERVAL_SECONDS = float(
    os.environ.get("ROBUSTA_CONFIG_WATCH_INTERVAL_SECONDS", "30")
)

# Keys of the Robusta config that Holmes actually consumes. The mounted
# active_playbooks.yaml also contains runner-only sections (e.g. playbooks),
# and we must not restart Holmes - killing in-flight investigations - when
# only those change.
_RELEVANT_KEYS = ("global_config", "sinks_config")


def compute_config_fingerprint(config_path: str) -> Optional[str]:
    """Fingerprint the parts of the Robusta config that Holmes reads.

    Returns None when the file is missing or unreadable. Falls back to
    hashing the whole file when it cannot be parsed as YAML.
    """
    try:
        with open(config_path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    try:
        content = yaml.safe_load(raw)
        relevant = {key: content.get(key) for key in _RELEVANT_KEYS}
        serialized = yaml.safe_dump(relevant, sort_keys=True).encode()
    except Exception:
        serialized = raw
    return hashlib.sha256(serialized).hexdigest()


def _default_on_change() -> None:
    # SIGTERM lets uvicorn shut down gracefully; kubernetes then restarts the
    # container, which re-reads the mounted config on startup.
    os.kill(os.getpid(), signal.SIGTERM)


def start_robusta_config_watcher(
    config_path: str = ROBUSTA_CONFIG_PATH,
    on_change: Callable[[], None] = _default_on_change,
    poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
    stop_event: Optional[threading.Event] = None,
) -> Optional[threading.Thread]:
    """Restart Holmes when the mounted Robusta config changes.

    Holmes reads settings such as cluster_name from the Robusta config secret
    once at startup, so a `helm upgrade` that changes them (e.g. renaming the
    cluster) otherwise leaves Holmes running with stale values until someone
    restarts it by hand. Kubelet keeps the mounted secret file up to date, so
    polling its content is enough to notice the change.

    No-op (returns None) when the config file does not exist, i.e. when
    running outside a Robusta installation.
    """
    initial_fingerprint = compute_config_fingerprint(config_path)
    if initial_fingerprint is None:
        logging.debug(
            f"No Robusta config at {config_path}; config watcher not started"
        )
        return None

    stop = stop_event or threading.Event()

    def watch() -> None:
        fingerprint = initial_fingerprint
        while not stop.wait(poll_interval_seconds):
            current = compute_config_fingerprint(config_path)
            if current is None or current == fingerprint:
                continue
            logging.info(
                f"Robusta config at {config_path} changed (e.g. cluster_name); "
                "restarting Holmes to apply the new configuration"
            )
            on_change()
            return

    thread = threading.Thread(
        target=watch, name="robusta-config-watcher", daemon=True
    )
    thread.start()
    logging.info(f"Watching {config_path} for Robusta config changes")
    return thread
