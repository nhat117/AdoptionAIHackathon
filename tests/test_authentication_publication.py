"""Offline archive fidelity and restoration isolation checks; no inference."""

import base64
import fcntl
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

REPORT = Path(__file__).parents[1] / "reports/authentication-diagnostic-v1"


def load(name):
    spec = importlib.util.spec_from_file_location(
        "publication_test_" + name, REPORT / (name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def record(path, content=b"raw\r\n\x00\xff"):
    return dict(
        path=path,
        content_base64=base64.b64encode(content).decode("ascii"),
        sha256=hashlib.sha256(content).hexdigest(),
    )


def setup_restore(tmp_path, monkeypatch, rows):
    module = load("restore")
    report = tmp_path / "reports/authentication-diagnostic-v1"
    report.mkdir(parents=True)
    monkeypatch.setattr(module, "__file__", str(report / "restore.py"))
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "RUN", tmp_path / "runs/authentication-diagnostic-v1")
    with gzip.open(report / "raw-records.jsonl.gz", "wt") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return module


def test_publish_restore_binary_roundtrip(tmp_path, monkeypatch):
    publisher = load("publish")
    origin = tmp_path / "origin"
    origin.mkdir()
    monkeypatch.chdir(origin)
    root = Path("runs/authentication-diagnostic-v1")
    root.mkdir(parents=True)
    content = b"first\r\nsecond\n\x00\xff"
    (root / "binary.json").write_bytes(content)
    report = origin / "reports/authentication-diagnostic-v1"
    report.mkdir(parents=True)
    plan = dict(jobs=[])
    (report / "plan.json").write_text(json.dumps(plan))
    monkeypatch.setattr(publisher, "HERE", report)
    monkeypatch.setattr(
        publisher.analysis,
        "analyze",
        lambda _: dict(rows=[], rates=[], paired_wording_contrasts=[], budget={}),
    )
    monkeypatch.setattr(publisher.analysis.run, "frozen", lambda: (plan, {}))
    monkeypatch.setattr(publisher, "draw", lambda *args: None)
    publisher.publish(root)
    with gzip.open(report / "raw-records.jsonl.gz", "rt") as f:
        rows = [json.loads(line) for line in f]
    destination = tmp_path / "destination"
    destination.mkdir()
    restorer = setup_restore(destination, monkeypatch, rows)
    restorer.restore()
    assert (restorer.RUN / "binary.json").read_bytes() == content
    restorer.restore()  # Identical existing records are safe.


@pytest.mark.parametrize(
    "paths",
    [
        ["runs/authentication-diagnostic-v1/a", "runs/authentication-diagnostic-v1/a"],
        ["/tmp/escape"],
        ["runs/authentication-diagnostic-v1/../escape"],
        ["runs/authentication-diagnostic-v1"],
    ],
)
def test_reject_invalid_destinations_before_data_write(tmp_path, monkeypatch, paths):
    module = setup_restore(tmp_path, monkeypatch, [record(p) for p in paths])
    with pytest.raises(ValueError):
        module.restore()
    assert list(module.RUN.rglob("*")) == [module.RUN / "collector.lock"]


def test_reject_symlink_escape(tmp_path, monkeypatch):
    module = setup_restore(
        tmp_path, monkeypatch, [record("runs/authentication-diagnostic-v1/link/escape")]
    )
    module.RUN.mkdir(parents=True)
    (module.RUN / "link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        module.restore()
    assert not (tmp_path / "escape").exists()


def test_reject_symlinked_run_root(tmp_path, monkeypatch):
    module = setup_restore(tmp_path, monkeypatch, [])
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    module.RUN.parent.mkdir(parents=True)
    module.RUN.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        module.restore()
    assert not (outside / "collector.lock").exists()


def test_reject_differing_existing_record(tmp_path, monkeypatch):
    module = setup_restore(
        tmp_path, monkeypatch, [record("runs/authentication-diagnostic-v1/a")]
    )
    module.RUN.mkdir(parents=True)
    target = module.RUN / "a"
    target.write_bytes(b"existing")
    with pytest.raises(ValueError):
        module.restore()
    assert target.read_bytes() == b"existing"


def test_restore_respects_collector_lock(tmp_path, monkeypatch):
    module = setup_restore(
        tmp_path, monkeypatch, [record("runs/authentication-diagnostic-v1/a")]
    )
    module.RUN.mkdir(parents=True)
    with (module.RUN / "collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            module.restore()
    assert not (module.RUN / "a").exists()


def test_reject_tampered_archive_record(tmp_path, monkeypatch):
    row = record("runs/authentication-diagnostic-v1/a")
    row["sha256"] = "0" * 64
    module = setup_restore(tmp_path, monkeypatch, [row])
    with pytest.raises(ValueError):
        module.restore()
    assert not (module.RUN / "a").exists()
