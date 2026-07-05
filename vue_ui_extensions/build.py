"""Build hook for vue_ui_extensions."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from vue_ui_extensions.registry import discover_build_targets, get_app_root
from vue_ui_extensions.utils.node_runner import run_node_script


def get_bench_path() -> Path:
	bench_path = os.environ.get("BENCH_PATH")
	if bench_path:
		return Path(bench_path)
	return get_app_root().parent.parent.parent


def get_build_script() -> Path:
	return get_app_root().parent / "frontend" / "scripts" / "build-all.mjs"


def _numbered_target_choices(available_targets: list[dict]) -> tuple[dict[str, str], str]:
	"""Map prompt input (number or app name) to app_name or 'all'; return default key."""
	choices: dict[str, str] = {}
	for index, target in enumerate(available_targets, start=1):
		key = str(index)
		name = target["app_name"]
		choices[key] = name
		choices[name] = name
	all_key = str(len(available_targets) + 1)
	choices[all_key] = "all"
	choices["all"] = "all"
	return choices, all_key


def _echo_numbered_target_menu(available_targets: list[dict]) -> None:
	click.echo(click.style("\nVue UI Extensions — select app to build:", fg="cyan"))
	for index, target in enumerate(available_targets, start=1):
		click.echo(f"  {index}) {target['app_name']}")
	click.echo(f"  {len(available_targets) + 1}) all")


def select_build_targets(available_targets: list[dict]) -> list[dict]:
	"""Pick targets to build — prompt in TTY, otherwise use env or build all."""
	if not available_targets:
		return []

	env_value = os.environ.get("VUE_EXT_TARGETS") or os.environ.get("VUE_EXT_TARGET")
	if env_value:
		names = {name.strip() for name in env_value.split(",") if name.strip()}
		if "all" in names:
			return available_targets
		selected = [target for target in available_targets if target["app_name"] in names]
		if not selected:
			known = ", ".join(target["app_name"] for target in available_targets)
			raise ValueError(f"No matching Vue extension targets for {names!r}. Available: {known}")
		return selected

	if os.environ.get("VUE_EXT_BUILD_ALL") == "1":
		return available_targets

	if not sys.stdin.isatty():
		return available_targets

	choices, default_key = _numbered_target_choices(available_targets)
	_echo_numbered_target_menu(available_targets)
	choice = click.prompt(
		"Target",
		type=click.Choice(list(choices.keys()), case_sensitive=False),
		default=default_key,
		show_choices=False,
	)

	resolved = choices[choice]
	if resolved == "all":
		return available_targets
	return [target for target in available_targets if target["app_name"] == resolved]


def after_build() -> None:
	"""Frappe after_build hook — rebuild extended Vue apps when overrides exist."""
	targets = discover_build_targets(get_bench_path())
	if not targets:
		click.echo(click.style("vue_ui_extensions: no overrides found, skipping Vue build", fg="yellow"))
		return

	selected = select_build_targets(targets)
	if not selected:
		click.echo(click.style("vue_ui_extensions: no targets selected, skipping Vue build", fg="yellow"))
		return

	names = ", ".join(target["app_name"] for target in selected)
	click.echo(click.style(f"\nBuilding Vue UI extensions for: {names}", fg="cyan"))
	click.echo("Preparing workspace and starting Vite (first output may take a few seconds)...")
	run_build(selected)
	click.echo(click.style("Vue UI extensions built successfully", fg="green"))


def run_build(targets: list[dict] | None = None) -> None:
	script = get_build_script()
	if not script.exists():
		raise FileNotFoundError(f"Build script not found: {script}")

	env = os.environ.copy()
	env["BENCH_PATH"] = str(get_bench_path())
	if targets:
		env["VUE_EXT_TARGETS"] = ",".join(target["app_name"] for target in targets)

	run_node_script(script, script.parent.parent, extra_env=env)


def build_target(target_name: str) -> None:
	"""Bench execute entrypoint for a single target build."""
	script = get_app_root().parent / "frontend" / "scripts" / "build-target.mjs"
	env = os.environ.copy()
	env["BENCH_PATH"] = str(get_bench_path())
	env["VUE_EXT_TARGET"] = target_name
	run_node_script(script, script.parent.parent, extra_env=env)


if __name__ == "__main__":
	run_build()
	sys.exit(0)
