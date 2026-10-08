import os
import stat
import subprocess
from pathlib import Path

import pytest


@pytest.mark.linux_only
def test_stage2_sets_node_extra_ca_to_sandbox_ca(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"
    logs_dir = sandbox_root / "root" / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "slirp.ready").write_text("ready\n", encoding="utf-8")

    capture_path = tmp_path / "bwrap-args.txt"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_bwrap = bin_dir / "bwrap"
    fake_bwrap.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\0' \"$@\" > \"$DEV_SANDBOX_CAPTURE_BWRAP_ARGS\"\n",
        encoding="utf-8",
    )
    fake_bwrap.chmod(fake_bwrap.stat().st_mode | stat.S_IXUSR)

    repo_root = Path(__file__).resolve().parent.parent
    stage2 = repo_root / "scripts" / "sandbox" / "stage2-run.sh"
    env = os.environ.copy()
    env.update(
        {
            "DEV_SANDBOX_ROOT": str(sandbox_root),
            "DEV_SANDBOX_BASH": "/usr/bin/bash",
            "DEV_SANDBOX_INTERACTIVE": "false",
            "DEV_SANDBOX_USER": "hermes",
            "DEV_SANDBOX_HOME": "/home/hermes",
            "DEV_SANDBOX_CAPTURE_BWRAP_ARGS": str(capture_path),
            "PATH": f"{bin_dir}:{env.get('PATH', '')}",
        }
    )

    proc = subprocess.run([str(stage2)], env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

    args = capture_path.read_bytes().split(b"\0")
    for idx, arg in enumerate(args):
        if arg == b"--setenv" and idx + 2 < len(args) and args[idx + 1] == b"NODE_EXTRA_CA_CERTS":
            assert args[idx + 2] == b"/work/certs/ca.pem"
            break
    else:
        pytest.fail("NODE_EXTRA_CA_CERTS was not set by stage2-run.sh")
