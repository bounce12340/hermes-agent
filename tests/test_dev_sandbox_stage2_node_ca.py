"""Stage-2 sandbox must trust the sandbox MITM CA for Node HTTPS clients."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGE2 = REPO_ROOT / "scripts" / "sandbox" / "stage2-run.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


def test_stage2_sets_node_extra_ca_to_sandbox_ca(tmp_path: Path):
    root = tmp_path / "sandbox"
    (root / "root" / "logs").mkdir(parents=True)
    (root / "root" / "usr" / "bin").mkdir(parents=True)
    (root / "root" / "usr" / "local").mkdir(parents=True)
    (root / "home").mkdir(parents=True)
    (root / "etc").mkdir(parents=True)
    (root / "root" / "logs" / "slirp.ready").write_text("ok\n")
    (root / "root" / "usr" / "bin" / "ssh").write_text("#!/bin/sh\nexit 0\n")

    fake_bwrap = tmp_path / "bwrap"
    fake_bwrap.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n")
    fake_bwrap.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    env["DEV_SANDBOX_ROOT"] = str(root)
    env["DEV_SANDBOX_BASH"] = "/usr/bin/bash"
    env["DEV_SANDBOX_INTERACTIVE"] = "false"
    env["DEV_SANDBOX_USER"] = "hermes"
    env["DEV_SANDBOX_HOME"] = "/home/hermes"
    run = subprocess.run(
        ["bash", str(STAGE2), "echo", "ok"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    args = run.stdout.splitlines()
    idx = args.index("NODE_EXTRA_CA_CERTS")
    assert args[idx + 1] == "/work/certs/ca.pem"
