# CLAUDE.md

## Hard rule: never hardcode local machine paths

Never hardcode an absolute path to something on the developer's local
machine (e.g. `/Users/<name>/...`, `/Users/codebuilder/Documents/dev_projects/...`)
anywhere in tracked files — not in `pyproject.toml`, not in `tools/*.py`, not
in comments. This repo is public and shared; a personal path breaks the
build/CI for every other contributor and can leak unrelated private-project
directory structure. If a build step needs an external dependency's location,
take it from an environment variable with no baked-in default, or document
it in README.md as something the developer must set locally.

## Hard rule: never add GPU options to `pyproject.toml`

`pyproject.toml` (the `[tool.cibuildwheel.*]` sections) must never gain
GPU/backend-specific content: no `--gpu=...` flags in `before-all`, no
`WGPU_XCFRAMEWORK`/`VULKAN`/GL-backend environment variables, no GPU-related
`repair-wheel-command` changes, no hardcoded absolute paths to other local
projects (e.g. anything under a personal `Documents/dev_projects/...` tree).

GPU backend selection belongs in `tools/build_thorvg.py` / `setup.py` (via
env vars like `THORVG_GPU`) or in CI workflow files — never wired directly
into `pyproject.toml`'s cibuildwheel config. This keeps the default wheel
build portable and CPU-only; GPU builds are opted into elsewhere.

This was violated once (commit `083c8f6` area / a since-reverted working-tree
change) by hardcoding a personal machine path
(`/Users/codebuilder/Documents/dev_projects/nucleant_dev/NucleantVulkan/...`)
into `pyproject.toml`'s iOS `environment`/`repair-wheel-command`. That breaks
the build for every other contributor and CI, and leaks unrelated private
project paths into a public repo. Do not repeat this — if GPU/Vulkan/WebGPU
support needs wiring for a build, do it in `tools/build_thorvg.py` or a
CI-only override, and leave `pyproject.toml` alone.
