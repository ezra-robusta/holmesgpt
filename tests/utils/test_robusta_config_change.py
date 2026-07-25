import pytest
import yaml
from fastapi.testclient import TestClient

from holmes.common import env_vars
from holmes.utils import robusta_config_change
from holmes.utils.robusta_config_change import (
    record_robusta_config_fingerprint,
    robusta_config_changed,
)

CLUSTER = "prod-us-west-2"


@pytest.fixture(autouse=True)
def reset_recorded_fingerprint():
    """The recorded fingerprint is process-wide; don't leak it to other tests."""
    yield
    robusta_config_change._startup_fingerprint = None
    robusta_config_change._cache_key = None
    robusta_config_change._cache_value = None


def _write_config(path, cluster_name=CLUSTER, playbooks=None, sinks=None):
    path.write_text(
        yaml.dump(
            {
                "global_config": {"cluster_name": cluster_name},
                "sinks_config": sinks
                if sinks is not None
                else [{"robusta_sink": {"name": "robusta_ui_sink", "token": "abc"}}],
                "active_playbooks": playbooks if playbooks is not None else [],
            }
        )
    )
    return path


def _use_config(monkeypatch, path):
    monkeypatch.setattr(env_vars, "ROBUSTA_CONFIG_PATH", str(path))


def test_no_mounted_config_never_reports_a_change(monkeypatch, tmp_path):
    """CLI and standalone installs have no mounted secret - nothing to watch."""
    _use_config(monkeypatch, tmp_path / "missing.yaml")

    record_robusta_config_fingerprint()

    assert robusta_config_changed() is False


def test_unchanged_config_reports_no_change(monkeypatch, tmp_path):
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)

    record_robusta_config_fingerprint()

    assert robusta_config_changed() is False


def test_cluster_name_change_is_detected(monkeypatch, tmp_path):
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    _write_config(config, cluster_name=f"{CLUSTER}-v2")

    assert robusta_config_changed() is True


def test_sink_token_change_is_detected(monkeypatch, tmp_path):
    """Holmes reads its Robusta UI token from sinks_config at startup too."""
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    _write_config(
        config, sinks=[{"robusta_sink": {"name": "robusta_ui_sink", "token": "xyz"}}]
    )

    assert robusta_config_changed() is True


def test_playbook_only_change_is_ignored(monkeypatch, tmp_path):
    """Playbooks belong to robusta-runner; editing them must not restart Holmes."""
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    _write_config(config, playbooks=[{"triggers": [{"on_job_failure": {}}]}])

    assert robusta_config_changed() is False


def test_unrelated_sink_change_is_ignored(monkeypatch, tmp_path):
    """Holmes only reads its own robusta_sink token; other sinks are the runner's."""
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    _write_config(
        config,
        sinks=[
            {"robusta_sink": {"name": "robusta_ui_sink", "token": "abc"}},
            {"slack_sink": {"name": "slack sink", "slack_channel": "#alerts"}},
        ],
    )

    assert robusta_config_changed() is False


def test_unreadable_config_is_not_treated_as_a_change(monkeypatch, tmp_path):
    """A transient read/parse error must not restart the pod."""
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    config.write_text("{ this is not: valid: yaml")

    assert robusta_config_changed() is False


def test_deleted_config_is_not_treated_as_a_change(monkeypatch, tmp_path):
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    config.unlink()

    assert robusta_config_changed() is False


@pytest.mark.parametrize(
    "hostile_global_config",
    [
        pytest.param({"2026-01-01": "low"}, id="unquoted-date-key"),
        pytest.param({"a": 1, True: 2}, id="mixed-str-and-bool-keys"),
        pytest.param({"a": 1, 2: "b"}, id="mixed-str-and-int-keys"),
    ],
)
def test_yaml_keys_that_json_cannot_serialize_do_not_raise(
    monkeypatch, tmp_path, hostile_global_config
):
    """These are valid YAML and the runner accepts them.

    json.dumps rejects non-str keys outright and can't sort mixed-type keys, so
    letting it raise here would fail the liveness probe -- and, because the
    fingerprint is also recorded at import, would boot-loop the pod.
    """
    config = tmp_path / "active_playbooks.yaml"
    config.write_text(
        yaml.dump(
            {
                "global_config": {
                    "cluster_name": CLUSTER,
                    "custom_severity_map": hostile_global_config,
                },
                "sinks_config": [{"robusta_sink": {"token": "abc"}}],
            }
        )
    )
    _use_config(monkeypatch, config)

    record_robusta_config_fingerprint()

    assert robusta_config_changed() is False


def test_runner_only_global_config_keys_are_ignored(monkeypatch, tmp_path):
    """Holmes reads only cluster_name from global_config.

    prometheus_url, grafana_api_key and friends belong to robusta-runner;
    restarting Holmes when they change would kill investigations for nothing.
    """
    config = tmp_path / "active_playbooks.yaml"
    base = {
        "global_config": {"cluster_name": CLUSTER, "prometheus_url": "http://a"},
        "sinks_config": [{"robusta_sink": {"token": "abc"}}],
    }
    config.write_text(yaml.dump(base))
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    base["global_config"]["prometheus_url"] = "http://b"
    base["global_config"]["grafana_api_key"] = "rotated"
    config.write_text(yaml.dump(base))

    assert robusta_config_changed() is False


def test_signing_key_rotation_is_ignored(monkeypatch, tmp_path):
    """oauth_token_store re-reads signing_key from disk on every use."""
    config = tmp_path / "active_playbooks.yaml"
    base = {
        "global_config": {"cluster_name": CLUSTER, "signing_key": "old"},
        "sinks_config": [{"robusta_sink": {"token": "abc"}}],
    }
    config.write_text(yaml.dump(base))
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    base["global_config"]["signing_key"] = "new"
    config.write_text(yaml.dump(base))

    assert robusta_config_changed() is False


def test_config_appearing_after_startup_is_detected(monkeypatch, tmp_path):
    """The secret volume is optional; a pod can boot before it is projected.

    Such a pod started with no cluster name at all, so it must restart once the
    config shows up rather than stay blind for its whole lifetime.
    """
    config = tmp_path / "active_playbooks.yaml"
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    _write_config(config)

    assert robusta_config_changed() is True


def test_fingerprint_is_not_recomputed_while_the_file_is_untouched(
    monkeypatch, tmp_path
):
    """The probe runs every ~10s against a file that can approach 1MiB."""
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    parses = {"n": 0}
    real_safe_load = robusta_config_change.yaml.safe_load

    def counting_safe_load(*args, **kwargs):
        parses["n"] += 1
        return real_safe_load(*args, **kwargs)

    monkeypatch.setattr(robusta_config_change.yaml, "safe_load", counting_safe_load)

    for _ in range(5):
        assert robusta_config_changed() is False
    assert parses["n"] == 0, "unchanged file should not be re-parsed"

    # Positive control: proves the counter is actually wired to the parse, so
    # the assertion above can't pass just because the patch missed.
    _write_config(config, cluster_name=f"{CLUSTER}-v2")
    assert robusta_config_changed() is True
    assert parses["n"] == 1, "a changed file must be re-parsed"


def test_healthz_fails_once_the_mounted_config_changed(monkeypatch, tmp_path):
    """The liveness probe is what makes Kubernetes restart Holmes (ROB-601)."""
    from server import app

    client = TestClient(app)
    config = _write_config(tmp_path / "active_playbooks.yaml")
    _use_config(monkeypatch, config)
    record_robusta_config_fingerprint()

    assert client.get("/healthz").status_code == 200

    # helm upgrade --set clusterName=... rewrites the mounted secret
    _write_config(config, cluster_name=f"{CLUSTER}-v2")
    response = client.get("/healthz")

    assert response.status_code == 503
    assert "awaiting restart" in response.json()["detail"]
