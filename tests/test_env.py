"""Phase 11: .env handling (backend/env.py) + SOMIZ_DB resolution.

The backend never hardcodes configuration. This module covers the loader's
parsing and precedence rules (real environment variables always win over the
file) plus the default database path override.
"""

from __future__ import annotations

import os

from backend.database import default_db_path
from backend.env import load_dotenv, parse_dotenv


def test_parse_dotenv_basic():
    env = parse_dotenv(
        "SOMIZ_SIM_SEED=42\n"
        'SOMIZ_LABEL="french wording ok"\n'
        "# comment line\n"
        "\n"
        "export SOMIZ_EXPORTED=value\n"
        "SOMIZ_QUOTED='single quoted'\n"
    )
    assert env["SOMIZ_SIM_SEED"] == "42"
    assert env["SOMIZ_LABEL"] == "french wording ok"
    assert env["SOMIZ_EXPORTED"] == "value"
    assert env["SOMIZ_QUOTED"] == "single quoted"


def test_parse_dotenv_ignores_garbage_lines():
    env = parse_dotenv("NOT_A_KEY_VALUE\n= orphan\n# nope\nSOMIZ_OK=1\n")
    assert env == {"SOMIZ_OK": "1"}


def test_load_dotenv_sets_unset_vars(tmp_path, monkeypatch):
    monkeypatch.delenv("SOMIZ_TEST_A", raising=False)
    monkeypatch.delenv("SOMIZ_TEST_B", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SOMIZ_TEST_A=from-file\nSOMIZ_TEST_B=also\n")
    applied = load_dotenv(env_file)
    assert os.environ["SOMIZ_TEST_A"] == "from-file"
    assert applied == {"SOMIZ_TEST_A": "from-file", "SOMIZ_TEST_B": "also"}


def test_load_dotenv_never_overrides_real_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SOMIZ_TEST_A", "from-shell")
    monkeypatch.delenv("SOMIZ_TEST_B", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SOMIZ_TEST_A=from-file\nSOMIZ_TEST_B=file-only\n")
    applied = load_dotenv(env_file)
    assert os.environ["SOMIZ_TEST_A"] == "from-shell"
    assert os.environ["SOMIZ_TEST_B"] == "file-only"
    assert "SOMIZ_TEST_A" not in applied   # file did NOT override the shell


def test_load_dotenv_missing_file_is_noop(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}


def test_default_db_path_respects_somiz_db_env(monkeypatch):
    monkeypatch.setenv("SOMIZ_DB", "/tmp/override-somiz.db")
    assert default_db_path() == "/tmp/override-somiz.db"


def test_default_db_path_defaults_to_repo_data_dir(monkeypatch):
    monkeypatch.delenv("SOMIZ_DB", raising=False)
    assert default_db_path().endswith("data/somiz.db")