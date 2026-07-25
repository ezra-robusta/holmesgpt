import yaml
from fastapi.testclient import TestClient

from holmes.common import env_vars
from holmes.utils.robusta_config_change import (
    record_robusta_config_fingerprint,
    robusta_config_changed,
)

CLUSTER = "prod-us-west-2"


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
