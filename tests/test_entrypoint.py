import os
import shutil
import subprocess
import sys
from pathlib import Path

from pbirs_mailer.app import browser_launch_error_message


def test_main_loads_src_package_without_installation(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "config.json"
    shutil.copyfile(project_root / "config.example.json", config_path)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(project_root / "main.py"),
            "--config",
            str(config_path),
            "--dry-run",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Configuration valide : Example report" in result.stderr


def test_browser_profile_lock_has_actionable_message() -> None:
    error = RuntimeError(
        "BrowserType.launch: Opening in existing browser session. "
        "This usually means that the profile is already in use."
    )

    message = browser_launch_error_message(error)

    assert "Fermez toutes les fenêtres" in message
    assert "profil" in message
