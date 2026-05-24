"""Inject libthorvg-1.so into thorvg-cython Android wheels.

After cibuildwheel builds the wheel, this script adds libthorvg-1.so to
.libs/{abi}/ inside the wheel zip so ksproject/gradle picks it up as a
JNI library.  Gradle places it in the APK's lib/{abi}/ directory, where
Android's linker resolves it at runtime when the Python extension is loaded.

Usage:
    THORVG_LIB_DIR=thorvg/output python3 tools/add_android_libs.py <wheels_dir>

THORVG_LIB_DIR should point to the thorvg output root.  libthorvg-1.so is
expected at:
    $THORVG_LIB_DIR/android_{arch}/libthorvg-1.so   (e.g. android_aarch64/)
    $THORVG_LIB_DIR/libthorvg-1.so                  (flat fallback)
"""
import base64
import hashlib
import os
import sys
import zipfile
from pathlib import Path

_THORVG_SO = "libthorvg-1.so"

_ABI_TO_ARCH = {
    "arm64-v8a": "aarch64",
    "x86_64":    "x86_64",
}


def _abi_from_wheel(name: str) -> str | None:
    if "arm64_v8a" in name or "aarch64" in name:
        return "arm64-v8a"
    if "x86_64" in name:
        return "x86_64"
    return None


def add_libs_to_wheels(wheels_dir: str) -> None:
    lib_base = Path(os.environ.get("THORVG_LIB_DIR", "thorvg/output"))

    for wheel in sorted(Path(wheels_dir).glob("*.whl")):
        abi = _abi_from_wheel(wheel.name)
        if not abi:
            print(f"  Cannot determine ABI from {wheel.name}, skipping.")
            continue

        arch = _ABI_TO_ARCH[abi]
        so_path = lib_base / f"android_{arch}" / _THORVG_SO
        if not so_path.exists():
            so_path = lib_base / _THORVG_SO
        if not so_path.exists():
            print(f"  WARNING: {_THORVG_SO} not found for {abi} (looked in {lib_base}), skipping.")
            continue

        data = so_path.read_bytes()
        digest = (
            base64.urlsafe_b64encode(hashlib.sha256(data).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        arcname = f".libs/{abi}/{_THORVG_SO}"

        # Read existing RECORD so we can append to it.
        dist_info_name = None
        record_data = ""
        with zipfile.ZipFile(wheel, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".dist-info/RECORD"):
                    dist_info_name = name
                    record_data = zf.read(name).decode("utf-8")
                    break

        with zipfile.ZipFile(wheel, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            print(f"  Adding {arcname} to {wheel.name}")
            zf.writestr(arcname, data)
            if dist_info_name:
                updated = record_data + f"{arcname},sha256={digest},{len(data)}\n"
                zf.writestr(dist_info_name, updated)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wheels_dir>")
        sys.exit(1)
    add_libs_to_wheels(sys.argv[1])
