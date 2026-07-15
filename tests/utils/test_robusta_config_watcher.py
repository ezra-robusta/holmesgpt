import threading

import pytest
import yaml

from holmes.utils.robusta_config_watcher import (
    compute_config_fingerprint,
    start_robusta_config_watcher,
)

BASE_CONFIG = {
    "global_config": {"cluster_name": "my-cluster", "account_id": "abc"},
    "sinks_config": [{"robusta_sink": {"name": "robusta_ui_sink", "token": "t1"}}],
    "active_playbooks": [{"triggers": [{"on_pod_crash_loop": {}}]}],
}


def write_config(path, config: dict) -> None:
    path.write_text(yaml.safe_dump(config))


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "active_playbooks.yaml"
    write_config(path, BASE_CONFIG)
    return path


def test_fingerprint_changes_on_cluster_name_change(config_file):
    before = compute_config_fingerprint(str(config_file))
    changed = {**BASE_CONFIG, "global_config": {**BASE_CONFIG["global_config"], "cluster_name": "renamed"}}
    write_config(config_file, changed)
    assert compute_config_fingerprint(str(config_file)) != before


def test_fingerprint_ignores_runner_only_sections(config_file):
    before = compute_config_fingerprint(str(config_file))
    changed = {**BASE_CONFIG, "active_playbooks": [{"triggers": [{"on_deployment_update": {}}]}]}
    write_config(config_file, changed)
    assert compute_config_fingerprint(str(config_file)) == before


def test_fingerprint_missing_file(tmp_path):
    assert compute_config_fingerprint(str(tmp_path / "nope.yaml")) is None


def test_fingerprint_unparseable_file_falls_back_to_content_hash(tmp_path):
    path = tmp_path / "active_playbooks.yaml"
    path.write_text("{{ not yaml")
    before = compute_config_fingerprint(str(path))
    assert before is not None
    path.write_text("{{ not yaml either")
    assert compute_config_fingerprint(str(path)) != before


def test_watcher_not_started_without_config_file(tmp_path):
    thread = start_robusta_config_watcher(config_path=str(tmp_path / "nope.yaml"))
    assert thread is None


def test_watcher_triggers_on_change(config_file):
    changed_event = threading.Event()
    stop_event = threading.Event()
    thread = start_robusta_config_watcher(
        config_path=str(config_file),
        on_change=changed_event.set,
        poll_interval_seconds=0.05,
        stop_event=stop_event,
    )
    assert thread is not None
    try:
        # unrelated change first: must NOT trigger a restart
        write_config(
            config_file,
            {**BASE_CONFIG, "active_playbooks": [{"triggers": [{"on_job_failure": {}}]}]},
        )
        assert not changed_event.wait(0.3)

        write_config(
            config_file,
            {**BASE_CONFIG, "global_config": {**BASE_CONFIG["global_config"], "cluster_name": "renamed"}},
        )
        assert changed_event.wait(2)
    finally:
        stop_event.set()
        thread.join(timeout=2)


def test_watcher_does_not_trigger_when_unchanged(config_file):
    changed_event = threading.Event()
    stop_event = threading.Event()
    thread = start_robusta_config_watcher(
        config_path=str(config_file),
        on_change=changed_event.set,
        poll_interval_seconds=0.05,
        stop_event=stop_event,
    )
    assert thread is not None
    try:
        write_config(config_file, BASE_CONFIG)  # rewrite with identical content
        assert not changed_event.wait(0.3)
    finally:
        stop_event.set()
        thread.join(timeout=2)
