#!/usr/bin/env python3
"""
Post-build script: inject xcframeworks into iOS wheels.

Supports two modes:

1) repair-wheel-command (cibuildwheel):
     python tools/add-ios-frameworks.py <wheel> <dest_dir> [--xcframework <path> ...]
   Copies the wheel to dest_dir and injects the xcframeworks.

2) batch (manual / CI post-step):
     python tools/add-ios-frameworks.py <wheels_dir> [--xcframework <path> ...]
   Patches every .whl in the directory in-place.

After patching, each iOS wheel contains:
    .frameworks/thorvg.xcframework/...
    .frameworks/libomp.xcframework/...

This follows the BeeWare convention where .frameworks/ at
site-packages level is discovered by the host Xcode project.

Note: ANGLE / EGL xcframeworks are NOT injected automatically.
Users who build with GPU support are responsible for distributing
the ANGLE xcframeworks (libEGL.xcframework, libGLESv2.xcframework)
themselves.
"""
import argparse
import os
import shutil
import tempfile
import zipfile


def _resolve_xcframeworks(cli_paths: list[str] | None) -> list[str]:
    """Resolve xcframework paths from CLI args or env vars."""
    result = []

    if cli_paths:
        result.extend(cli_paths)
    else:
        # Default: thorvg xcframework
        root = os.environ.get("THORVG_ROOT", "thorvg")
        output = os.path.join(root, "output")

        if "THORVG_XCFRAMEWORK" in os.environ:
            result.append(os.environ["THORVG_XCFRAMEWORK"])
        else:
            result.append(os.path.join(output, "thorvg.xcframework"))

        # libomp xcframework
        libomp_xcfw = os.environ.get(
            "LIBOMP_XCFRAMEWORK",
            os.path.join(output, "libomp.xcframework"),
        )
        if os.path.isdir(libomp_xcfw):
            result.append(libomp_xcfw)

    return result


def _inject_xcframework(whl_path: str, xcfw: str) -> int:
    """Rewrite a wheel with xcframework files injected. Returns number of files added.

    We rebuild the ZIP from scratch rather than using append mode ("a"), which
    can produce duplicate central-directory entries and corrupt archives that
    PyPI rejects ("Mis-matched data size").
    """
    new_entries: list[tuple[str, str]] = []  # (arcname, file_path)
    for root, _dirs, files in os.walk(xcfw):
        for fname in files:
            file_path = os.path.join(root, fname)
            arcname = os.path.join(
                ".frameworks",
                os.path.relpath(file_path, os.path.dirname(xcfw)),
            )
            new_entries.append((arcname, file_path))

    if not new_entries:
        return 0

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".whl", dir=os.path.dirname(whl_path))
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(whl_path, "r") as zf_in:
            with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf_out:
                for item in zf_in.infolist():
                    zf_out.writestr(item, zf_in.read(item))
                for arcname, file_path in new_entries:
                    zf_out.write(file_path, arcname)
        os.replace(tmp_path, whl_path)
    except Exception:
        os.unlink(tmp_path)
        raise

    return len(new_entries)


def _inject_all(whl_path: str, xcframeworks: list[str]) -> int:
    """Inject all xcframeworks into a wheel. Returns total files added."""
    total = 0
    for xcfw in xcframeworks:
        if not os.path.isdir(xcfw):
            print(f"  WARNING: xcframework not found, skipping: {xcfw}")
            continue
        n = _inject_xcframework(whl_path, xcfw)
        print(f"  -> added {n} files from {os.path.basename(xcfw)}")
        total += n
    return total


def repair_single_wheel(wheel: str, dest_dir: str, xcframeworks: list[str]) -> None:
    """cibuildwheel repair-wheel-command mode: copy wheel to dest_dir, then inject."""
    if not os.path.isfile(wheel):
        raise FileNotFoundError(f"Wheel not found: {wheel}")
    os.makedirs(dest_dir, exist_ok=True)
    dest_wheel = os.path.join(dest_dir, os.path.basename(wheel))
    shutil.copy2(wheel, dest_wheel)
    total = _inject_all(dest_wheel, xcframeworks)
    print(f"  Total: {total} framework files in {os.path.basename(dest_wheel)}")


def patch_wheels_dir(wheels_dir: str, xcframeworks: list[str]) -> None:
    """Batch mode: patch every .whl in a directory in-place."""
    if not os.path.isdir(wheels_dir):
        raise FileNotFoundError(f"Wheels directory not found: {wheels_dir}")
    for whl_name in sorted(os.listdir(wheels_dir)):
        if not whl_name.endswith(".whl"):
            continue
        whl_path = os.path.join(wheels_dir, whl_name)
        print(f"Patching {whl_name} ...")
        _inject_all(whl_path, xcframeworks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inject xcframeworks into iOS wheels (.frameworks/ folder)."
    )
    parser.add_argument(
        "positional",
        nargs="+",
        help="Either <wheel> <dest_dir> (repair mode) or <wheels_dir> (batch mode).",
    )
    parser.add_argument(
        "--xcframework",
        action="append",
        default=None,
        dest="xcframeworks",
        help="Path to an xcframework to inject (can be repeated).",
    )
    args = parser.parse_args()
    xcframeworks = _resolve_xcframeworks(args.xcframeworks)
    print(f"XCFrameworks to inject: {[os.path.basename(x) for x in xcframeworks]}")

    if len(args.positional) == 2 and args.positional[0].endswith(".whl"):
        # repair-wheel-command mode: <wheel> <dest_dir>
        repair_single_wheel(args.positional[0], args.positional[1], xcframeworks)
    elif len(args.positional) == 1 and os.path.isdir(args.positional[0]):
        # batch mode: <wheels_dir>
        patch_wheels_dir(args.positional[0], xcframeworks)
    else:
        parser.error(
            "Usage: script.py <wheel.whl> <dest_dir> [--xcframework ...]\n"
            "       script.py <wheels_dir> [--xcframework ...]"
        )
