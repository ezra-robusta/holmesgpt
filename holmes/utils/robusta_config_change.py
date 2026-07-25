"""Detect helm-driven changes to the Robusta config Holmes mounts.

Holmes reads its cluster name and its Robusta UI token out of the mounted
``robusta-playbooks-config-secret`` (``/etc/robusta/config/active_playbooks.yaml``)
exactly once, at process start. A ``helm upgrade`` that changes ``clusterName``
rewrites that secret and the kubelet refreshes the mounted file, but the Holmes
pod spec is untouched -- so nothing rolls the deployment and Holmes keeps
serving under the stale cluster name until someone restarts it by hand.

Rather than watch the file and terminate ourselves, we let Kubernetes do the
restart it already knows how to do: the liveness probe polls ``/healthz`` every
few seconds, so reporting unhealthy once the mounted config no longer matches
what we loaded is enough for the kubelet to restart the container against the
fresh config.

Only the parts of the file Holmes itself consumes are fingerprinted, so that
edits meant for robusta-runner -- playbooks above all, which it hot-reloads with
its own file watcher -- don't interrupt in-flight Holmes investigations. Where
there is a choice we watch a whole section rather than individual keys: a
needless restart on a helm upgrade is cheap, silently serving stale config is
not, and a section-level fingerprint doesn't rot when a new key is read.
"""

import hashlib
import json
import logging
import os
from typing import Optional

import yaml

from holmes.common import env_vars

_startup_fingerprint: Optional[str] = None


def _holmes_relevant_config(config: dict) -> dict:
    """The subset of active_playbooks.yaml that Holmes reads at startup."""
    sinks = config.get("sinks_config") or []
    return {
        # cluster_name and signing_key both live here.
        "global_config": config.get("global_config"),
        # Holmes only takes its Robusta UI token out of sinks_config; the other
        # sinks (slack, teams, jira, ...) are the runner's business.
        "robusta_sinks": [
            sink for sink in sinks if isinstance(sink, dict) and "robusta_sink" in sink
        ],
    }


def _fingerprint() -> Optional[str]:
    """Hash the watched sections of the mounted Robusta config.

    Returns None when there is nothing to compare against: no mounted config
    (CLI and standalone installs), or a file we cannot read or parse. Treating
    an unreadable file as "unchanged" is deliberate -- a transient read error
    must not be mistaken for a config change and restart the pod.
    """
    path = env_vars.ROBUSTA_CONFIG_PATH
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            watched = _holmes_relevant_config(yaml.safe_load(f) or {})
    except Exception:
        logging.warning("Could not fingerprint %s", path, exc_info=True)
        return None
    return hashlib.sha256(
        json.dumps(watched, sort_keys=True, default=str).encode()
    ).hexdigest()


def record_robusta_config_fingerprint() -> None:
    """Remember the mounted Robusta config as of process start."""
    global _startup_fingerprint
    _startup_fingerprint = _fingerprint()


def robusta_config_changed() -> bool:
    """True once the mounted Robusta config differs from what Holmes loaded."""
    if _startup_fingerprint is None:
        return False
    current = _fingerprint()
    if current is None or current == _startup_fingerprint:
        return False
    logging.warning(
        "%s changed since startup; reporting unhealthy so Kubernetes restarts "
        "Holmes with the new config",
        env_vars.ROBUSTA_CONFIG_PATH,
    )
    return True
