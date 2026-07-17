import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def run_init(
    tmp_path: Path, uv_venv_exit_code: int = 0, wget_exit_code: int = 0
) -> tuple[subprocess.CompletedProcess[str], Path]:
    home = tmp_path / "home"
    fake_bin = tmp_path / "bin"
    home.mkdir()
    fake_bin.mkdir()

    wget = fake_bin / "wget"
    wget.write_text(
        f"""#!/bin/sh
if [ {wget_exit_code} -ne 0 ]; then
  exit {wget_exit_code}
fi
output=
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-qO" ]; then
    output="$2"
    shift 2
  else
    shift
  fi
done
cat > "$output" <<'INSTALLER'
mkdir -p "$UV_INSTALL_DIR"
cat > "$UV_INSTALL_DIR/uv" <<'UV'
#!/bin/sh
printf 'uv %s\\n' "$*" >> "$HOME/invocations"
if [ "$1" = "venv" ]; then
  mkdir -p .venv/bin
  : > .venv/bin/activate
  exit {uv_venv_exit_code}
fi
UV
cat > "$UV_INSTALL_DIR/uvx" <<'UVX'
#!/bin/sh
printf 'uvx %s\\n' "$*" >> "$HOME/invocations"
UVX
chmod +x "$UV_INSTALL_DIR/uv" "$UV_INSTALL_DIR/uvx"
INSTALLER
"""
    )
    wget.chmod(0o755)

    for command in ("uv", "uvx"):
        fallback = fake_bin / command
        fallback.write_text(
            f"#!/bin/sh\nprintf 'fallback {command} %s\\n' \"$*\" >> \"$HOME/invocations\"\n"
        )
        fallback.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{fake_bin}:/usr/bin:/bin"

    result = subprocess.run(
        ["make", "-f", str(PROJECT_ROOT / "Makefile"), "init"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    return result, home


def test_init_uses_newly_installed_uv(tmp_path: Path):
    result, home = run_init(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (home / "invocations").read_text().splitlines() == [
        "uv venv",
        "uv sync",
        "uvx pyrefly init",
        "uvx mypy --version",
    ]


def test_init_stops_when_uv_setup_fails(tmp_path: Path):
    result, home = run_init(tmp_path, uv_venv_exit_code=7)

    assert result.returncode != 0
    assert (home / "invocations").read_text().splitlines() == ["uv venv"]


def test_init_stops_when_uv_download_fails(tmp_path: Path):
    result, home = run_init(tmp_path, wget_exit_code=23)

    assert result.returncode != 0
    assert not (home / "invocations").exists()
