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
    .frameworks/ThorVG.xcframework/...
    .frameworks/libomp.xcframework/...

This follows the BeeWare convention where .frameworks/ at
site-packages level is discovered by the host Xcode project.

ThorVG casing: thorvg-cython's own build (tools/build_thorvg.py) emits a
lowercase thorvg.xcframework/thorvg.framework/thorvg, matching upstream
ThorVG's naming. Nucleant's Swift-side package (NucleantThorVG) instead
ships ThorVG.xcframework/ThorVG.framework/ThorVG. Both can end up embedded
in the same app's Frameworks directory, and on the default case-insensitive
APFS volume "ThorVG.framework" and "thorvg.framework" collide -- whichever
copy lands second silently clobbers the other, which is what produced the
`Library not loaded: @rpath/ThorVG.framework/ThorVG` crash. To eliminate the
collision, this script renames the injected thorvg xcframework to ThorVG
everywhere (directory names, binary name, install name, Info.plist) and
retargets any compiled extension in the wheel that linked against the
original lowercase name, so nothing in the wheel still expects "thorvg".

Note: ANGLE / EGL xcframeworks are NOT injected automatically.
Users who build with GPU support are responsible for distributing
the ANGLE xcframeworks (libEGL.xcframework, libGLESv2.xcframework)
themselves.

NO_EMBED_FRAMEWORKS: when this env var is set (non-empty), no xcframework
files are injected into the wheel at all -- consumers such as NucleantSkia
build against thorvg-cython for its headers/extensions but bundle
ThorVG.xcframework and libomp.xcframework themselves (and get the wgpu
xcframeworks via NucleantVulkan), so embedding them here would just be
dead weight in the wheel. The compiled extensions still get their install
names retargeted from @rpath/thorvg.framework/thorvg to
@rpath/ThorVG.framework/ThorVG so they resolve against whatever framework
the consumer ends up bundling under the capitalized Nucleant convention.
"""
import argparse
import os
import plistlib
import shutil
import subprocess
import tempfile
import zipfile

OLD_INSTALL_NAME = "@rpath/thorvg.framework/thorvg"
NEW_INSTALL_NAME = "@rpath/ThorVG.framework/ThorVG"


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


def _is_thorvg_xcfw(xcfw: str) -> bool:
    return os.path.basename(os.path.normpath(xcfw)) == "thorvg.xcframework"


def _renamed_rel_path(rel_path: str) -> str:
    """thorvg.xcframework/<slice>/thorvg.framework/thorvg -> ThorVG equivalents."""
    parts = rel_path.split(os.sep)
    for i, part in enumerate(parts):
        if part == "thorvg.xcframework":
            parts[i] = "ThorVG.xcframework"
        elif part == "thorvg.framework":
            parts[i] = "ThorVG.framework"
        elif part == "thorvg" and i > 0 and parts[i - 1] == "ThorVG.framework":
            parts[i] = "ThorVG"
    return os.sep.join(parts)


def _zipinfo_for(file_path: str, arcname: str) -> zipfile.ZipInfo:
    st = os.stat(file_path)
    zi = zipfile.ZipInfo(arcname)
    zi.external_attr = (st.st_mode & 0xFFFF) << 16
    zi.compress_type = zipfile.ZIP_DEFLATED
    return zi


def _entry_bytes(file_path: str, renamed: bool) -> bytes:
    """Read file_path's bytes, patching the thorvg binary/Info.plist in place
    when it belongs to the renamed (ThorVG) xcframework."""
    fname = os.path.basename(file_path)

    if renamed and fname == "thorvg" and os.access(file_path, os.X_OK):
        tmp_fd, tmp = tempfile.mkstemp()
        os.close(tmp_fd)
        try:
            shutil.copy2(file_path, tmp)
            os.chmod(tmp, 0o755)
            subprocess.run(
                ["install_name_tool", "-id", NEW_INSTALL_NAME, tmp], check=True
            )
            with open(tmp, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp)

    if renamed and fname == "Info.plist":
        with open(file_path, "rb") as f:
            info = plistlib.load(f)
        if info.get("CFBundleExecutable") == "thorvg":
            info["CFBundleExecutable"] = "ThorVG"
        if info.get("CFBundleName") == "thorvg":
            info["CFBundleName"] = "ThorVG"
        return plistlib.dumps(info)

    with open(file_path, "rb") as f:
        return f.read()


def _inject_xcframework(whl_path: str, xcfw: str) -> int:
    """Rewrite a wheel with xcframework files injected. Returns number of files added.

    We rebuild the ZIP from scratch rather than using append mode ("a"), which
    can produce duplicate central-directory entries and corrupt archives that
    PyPI rejects ("Mis-matched data size").
    """
    renamed = _is_thorvg_xcfw(xcfw)
    new_entries: list[tuple[str, str]] = []  # (arcname, file_path)
    for root, _dirs, files in os.walk(xcfw):
        for fname in files:
            file_path = os.path.join(root, fname)
            rel = os.path.relpath(file_path, os.path.dirname(xcfw))
            if renamed:
                rel = _renamed_rel_path(rel)
            arcname = os.path.join(".frameworks", rel)
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
                    zi = _zipinfo_for(file_path, arcname)
                    zf_out.writestr(zi, _entry_bytes(file_path, renamed))
        os.replace(tmp_path, whl_path)
    except Exception:
        os.unlink(tmp_path)
        raise

    return len(new_entries)


def _retarget_extensions(whl_path: str) -> int:
    """Repoint any compiled extension in the wheel that still links the old
    lowercase @rpath/thorvg.framework/thorvg at the renamed ThorVG framework.
    Returns the number of extensions patched."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".whl", dir=os.path.dirname(whl_path))
    os.close(tmp_fd)
    patched = 0
    try:
        with zipfile.ZipFile(whl_path, "r") as zf_in:
            with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf_out:
                for item in zf_in.infolist():
                    data = zf_in.read(item)
                    if item.filename.endswith(".so") and not item.filename.startswith(".frameworks/"):
                        tmp_so_fd, tmp_so = tempfile.mkstemp(suffix=".so")
                        os.close(tmp_so_fd)
                        try:
                            with open(tmp_so, "wb") as f:
                                f.write(data)
                            os.chmod(tmp_so, 0o755)
                            check = subprocess.run(
                                ["otool", "-L", tmp_so], capture_output=True, text=True
                            )
                            if OLD_INSTALL_NAME in check.stdout:
                                subprocess.run(
                                    ["install_name_tool", "-change",
                                     OLD_INSTALL_NAME, NEW_INSTALL_NAME, tmp_so],
                                    check=True,
                                )
                                with open(tmp_so, "rb") as f:
                                    data = f.read()
                                patched += 1
                                print(f"  -> retargeted {item.filename} to {NEW_INSTALL_NAME}")
                        finally:
                            os.unlink(tmp_so)
                    zf_out.writestr(item, data)
        os.replace(tmp_path, whl_path)
    except Exception:
        os.unlink(tmp_path)
        raise
    return patched


def _inject_all(whl_path: str, xcframeworks: list[str]) -> int:
    """Inject all xcframeworks into a wheel. Returns total files added."""
    total = 0
    for xcfw in xcframeworks:
        if not os.path.isdir(xcfw):
            print(f"  WARNING: xcframework not found, skipping: {xcfw}")
            continue
        n = _inject_xcframework(whl_path, xcfw)
        label = "ThorVG.xcframework" if _is_thorvg_xcfw(xcfw) else os.path.basename(xcfw)
        print(f"  -> added {n} files from {label}")
        total += n
    _retarget_extensions(whl_path)
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
    if os.environ.get("NO_EMBED_FRAMEWORKS"):
        xcframeworks = []
        print("NO_EMBED_FRAMEWORKS set -- skipping xcframework embedding "
              "(consumer bundles thorvg/libomp/wgpu frameworks itself); "
              "extension install names will still be retargeted to ThorVG.framework")
    else:
        xcframeworks = _resolve_xcframeworks(args.xcframeworks)
        print(f"XCFrameworks to inject: {['ThorVG.xcframework' if _is_thorvg_xcfw(x) else os.path.basename(x) for x in xcframeworks]}")

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
