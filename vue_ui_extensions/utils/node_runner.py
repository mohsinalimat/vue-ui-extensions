"""Run trusted Node build scripts without direct subprocess usage in app code."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from frappe.commands import popen

from vue_ui_extensions.registry import get_app_root


def _resolve_trusted_script(script: Path) -> Path:
	script = script.resolve()
	app_root = get_app_root().parent.resolve()
	if not script.is_file():
		raise FileNotFoundError(f"Build script not found: {script}")
	try:
		script.relative_to(app_root)
	except ValueError as exc:
		raise ValueError(f"Build script must live under {app_root}") from exc
	return script


def _resolve_trusted_cwd(cwd: Path) -> Path:
	cwd = cwd.resolve()
	app_root = get_app_root().parent.resolve()
	try:
		cwd.relative_to(app_root)
	except ValueError as exc:
		raise ValueError(f"Build cwd must live under {app_root}") from exc
	return cwd


def run_node_script(script: Path, cwd: Path, extra_env: dict[str, str] | None = None) -> None:
	"""Execute a Node build script using a static argv list and validated paths."""
	node_bin = shutil.which("node")
	if not node_bin:
		raise RuntimeError("node executable not found on PATH")

	script = _resolve_trusted_script(script)
	cwd = _resolve_trusted_cwd(cwd)
	env = os.environ.copy()
	if extra_env:
		env.update(extra_env)

	returncode = popen(
		[node_bin, str(script)],
		shell=False,
		cwd=str(cwd),
		env=env,
		output=False,
		raise_err=False,
	)
	if returncode != 0:
		raise RuntimeError(f"Node build failed with exit code {returncode}")
