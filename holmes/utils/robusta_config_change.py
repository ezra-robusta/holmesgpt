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

We fingerprint only the two things Holmes actually latches at startup -- the
cluster name and the Robusta UI token. Everything else in that file is either
the runner's (playbooks, other sinks, and the many ``globalConfig`` keys like
``prometheus_url`` or ``grafana_api_key`` that Holmes never reads) or, in the
case of ``signing_key``, already re-read from disk on every use by
``oauth_token_store``. Restarting for any of those would kill in-flight
investigations for a change Holmes does not care about.

This code runs on every liveness probe and once at import, so it must never
raise: an exception here becomes a failed probe at best and a boot loop at
worst. Every failure mode degrades to "unchanged" instead.
"""

import hashlib
import json
import logging
import os
from typing import Optional

import yaml

from holmes.common import env_vars

# Sentinel for "no readable config file". Distinct from any sha256 so that a
# secret which shows up *after* boot still registers as a change.
_NO_CONFIG = "no-robusta-config"

_startup_fingerprint: Optional[str] = None

# (mtime_ns, size) -> fingerprint, so the probe doesn't re-parse the YAML every
# few seconds. The file can approach a Secret's ~1MiB, where parsing costs real
# CPU on a pod whose default request is 100m.
_cache_key: Optional[tuple] = None
_cache_value: Optional[str] = None


def _holmes_relevant_config(config: dict) -> dict:
    """The subset of active_playbooks.yaml that Holmes latches at startup."""
    global_config = config.get("global_config")
    if not isinstance(global_config, dict):
        global_config = {}
    sinks = config.get("sinks_config")
    if not isinstance(sinks, list):
        sinks = []
    return {
        "cluster_name": global_config.get("cluster_name"),
        # Holmes only takes its Robusta UI token out of sinks_config; the other
        # sinks (slack, teams, jira, ...) are the runner's business.
        "robusta_sinks": [
            sink for sink in sinks if isinstance(sink, dict) and "robusta_sink" in sink
        ],
    }


def _fingerprint() -> str:
    """Fingerprint the parts of the mounted Robusta config that Holmes reads.

    Returns ``_NO_CONFIG`` when there is no config file (CLI and standalone
    installs). If the file exists but cannot be read, parsed, or serialised,
    returns the last value we computed successfully -- a malformed or
    half-written file must not be mistaken for a config change.
    """
    global _cache_key, _cache_value
    path = env_vars.ROBUSTA_CONFIG_PATH
    try:
        stat = os.stat(path)
        cache_key = (stat.st_mtime_ns, stat.st_size)
        if cache_key == _cache_key and _cache_value is not None:
            return _cache_value
        with open(path) as f:
            watched = _holmes_relevant_config(yaml.safe_load(f) or {})
        # Keys in this file come from user-authored YAML and are not guaranteed
        # to be strings (an unquoted `2026-01-01:` parses to a date), which
        # json.dumps rejects outright -- sort_keys also can't order mixed types.
        # Hence the serialisation lives inside the try, not after it.
        fingerprint = hashlib.sha256(
            json.dumps(watched, sort_keys=True, default=str).encode()
        ).hexdigest()
    except FileNotFoundError:
        return _NO_CONFIG
    except Exception:
        logging.warning(
            "Could not fingerprint %s; treating the config as unchanged",
            path,
            exc_info=True,
        )
        return _cache_value if _cache_value is not None else _NO_CONFIG
    _cache_key, _cache_value = cache_key, fingerprint
    return fingerprint


def record_robusta_config_fingerprint() -> None:
    """Remember the mounted Robusta config as of process start."""
    global _startup_fingerprint
    _startup_fingerprint = _fingerprint()


def robusta_config_changed() -> bool:
    """True once the mounted Robusta config differs from what Holmes loaded."""
    if _startup_fingerprint is None:
        return False
    current = _fingerprint()
    # A config that has gone missing or unreadable is not grounds for a
    # restart: Holmes would only come back up with less than it has now.
    if current == _NO_CONFIG or current == _startup_fingerprint:
        return False
    logging.warning(
        "%s changed since startup; reporting unhealthy so Kubernetes restarts "
        "Holmes with the new config",
        env_vars.ROBUSTA_CONFIG_PATH,
    )
    return True
