#!/usr/bin/env python3
"""
setup.py for thorvg-cython.

Platform-aware linking against the thorvg shared library:
  - iOS   (sys.platform == "ios"):   link via libthorvg-1.dylib from XCFramework
  - macOS (sys.platform == "darwin"): link against libthorvg-1.dylib
  - Linux / other:                    link against libthorvg-1.so
  - Windows:                          link against thorvg-1.dll (import lib)
  - Android:                          link against libthorvg-1.so

The shared library is copied into the package directory and bundled into
the wheel so that the extension modules can find it at runtime via rpath.
"""
import os
import sys
import shutil
import subprocess

# ---------------------------------------------------------------------------
#  GPU mode detection
#
#  THORVG_GPU env var controls whether the real GlCanvas (gl_canvas.pyx) or
#  a stub (gl_canvas.py) is compiled.  Future values: "gl", "gles", "angle".
#  Any non-empty value enables GPU mode.
# ---------------------------------------------------------------------------
THORVG_GPU = os.environ.get("THORVG_GPU", "")
GPU_MODE = bool(THORVG_GPU)
VULKAN_MODE = THORVG_GPU == "vulkan"
GL_MODE = GPU_MODE and not VULKAN_MODE
import sysconfig
from pathlib import Path

from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize

# ---------------------------------------------------------------------------
#  Auto-detect SDKROOT on Apple platforms (macOS / iOS)
# ---------------------------------------------------------------------------
if sys.platform in ("darwin", "ios") and "SDKROOT" not in os.environ:
    _SDK_MAP = {
        "darwin": "macosx",
        "ios":    "iphoneos",
    }
    _xcode_pn = os.environ.get("PLATFORM_NAME", "")
    if "simulator" in _xcode_pn.lower():
        _sdk_name = "iphonesimulator"
    else:
        _sdk_name = _SDK_MAP.get(sys.platform, "macosx")
    try:
        sdk = subprocess.check_output(
            ["xcrun", "--sdk", _sdk_name, "--show-sdk-path"], text=True
        ).strip()
        if sdk:
            os.environ["SDKROOT"] = sdk
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

# ---------------------------------------------------------------------------
#  Resolve paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
THORVG_ROOT = Path(os.environ.get("THORVG_ROOT", HERE / "thorvg"))
if not THORVG_ROOT.is_absolute():
    THORVG_ROOT = (HERE / THORVG_ROOT).resolve()

THORVG_INCLUDE = os.environ.get(
    "THORVG_INCLUDE",
    str(THORVG_ROOT / "inc"),
)

def _resolve_lib_dir() -> str:
    env_val = os.environ.get("THORVG_LIB_DIR")
    if env_val:
        p = Path(env_val)
        if not p.is_absolute():
            p = (HERE / p).resolve()
        return str(p)
    for candidate in [
        THORVG_ROOT / "builddir_capi" / "src",
        THORVG_ROOT / "builddir" / "src",
        THORVG_ROOT / "build" / "src",
        THORVG_ROOT / "output",
    ]:
        if candidate.exists():
            return str(candidate)
    return str(THORVG_ROOT / "output")

THORVG_LIB_DIR = _resolve_lib_dir()

THORVG_XCFRAMEWORK = os.environ.get(
    "THORVG_XCFRAMEWORK",
    str(THORVG_ROOT / "output" / "thorvg.xcframework"),
)

LIBOMP_XCFRAMEWORK = os.environ.get(
    "LIBOMP_XCFRAMEWORK",
    str(THORVG_ROOT / "output" / "libomp.xcframework"),
)

ANGLE_LIB_DIR = os.environ.get(
    "ANGLE_LIB_DIR",
    str(THORVG_ROOT / "output" / "angle"),
)

THORVG_CAPI_INCLUDE = os.environ.get(
    "THORVG_CAPI_INCLUDE",
    str(THORVG_ROOT / "src" / "bindings" / "capi"),
)

# --- DEBUG: print resolved paths so CI logs show what's happening ----------
_capi_header = Path(THORVG_CAPI_INCLUDE) / "thorvg_capi.h"
print(f"[setup.py] HERE              = {HERE}")
print(f"[setup.py] THORVG_ROOT       = {THORVG_ROOT}  (exists={THORVG_ROOT.exists()})")
print(f"[setup.py] THORVG_INCLUDE    = {THORVG_INCLUDE}")
print(f"[setup.py] THORVG_CAPI_INCLUDE = {THORVG_CAPI_INCLUDE}")
print(f"[setup.py] thorvg_capi.h     = {_capi_header}  (exists={_capi_header.exists()})")
print(f"[setup.py] THORVG_LIB_DIR    = {THORVG_LIB_DIR}  (exists={Path(THORVG_LIB_DIR).exists()})")
if THORVG_ROOT.exists():
    print(f"[setup.py] THORVG_ROOT ls    = {list(THORVG_ROOT.iterdir())}")

# ---------------------------------------------------------------------------
#  Platform detection helpers
# ---------------------------------------------------------------------------
PLATFORM = sys.platform
_xcode_platform = os.environ.get("PLATFORM_NAME", "")
_host_platform = os.environ.get("_PYTHON_HOST_PLATFORM", "")
_archflags = os.environ.get("ARCHFLAGS", "")

def _is_ios_build() -> bool:
    if PLATFORM == "ios":
        return True
    if "iphone" in _xcode_platform.lower():
        return True
    if "ios" in _host_platform.lower():
        return True
    return False

def _is_macos_build() -> bool:
    if PLATFORM == "darwin":
        return True
    if "macos" in _xcode_platform.lower():
        return True
    return False

def _is_android_build() -> bool:
    if PLATFORM == "android":
        return True
    if "android" in _host_platform.lower():
        return True
    return False

def _get_arch() -> str:
    if _archflags:
        for part in _archflags.split():
            if part in ("arm64", "x86_64", "aarch64"):
                return "arm64" if part == "aarch64" else part
    machine = sysconfig.get_config_var("HOST_GNU_TYPE") or ""
    if "aarch64" in machine or "arm64" in machine:
        return "arm64"
    if "x86_64" in machine:
        return "x86_64"
    import platform as _plat
    return _plat.machine()

# ---------------------------------------------------------------------------
#  Package source directory (where we copy the shared lib for bundling)
# ---------------------------------------------------------------------------
_PKG_SRC = HERE / "src" / "thorvg_cython"


def _bundle_dylib(src_path: Path, dest_dir: Path) -> None:
    """Copy a shared library into dest_dir for wheel bundling.

    On macOS/iOS this also creates a versioned symlink if the install name
    references a versioned filename (e.g. libthorvg-1.1.dylib), and fixes
    the install_name to use @rpath/<basename> so delocate/the loader works.

    Always overwrites an existing file — when cibuildwheel builds multiple
    architectures they share the source tree, so each build must place the
    correct arch's library.
    """
    dest = dest_dir / src_path.name
    # Always follow symlinks (copy the real file)
    real_src = src_path.resolve()
    shutil.copy2(str(real_src), str(dest))
    print(f"[setup.py] Copied {src_path.name} -> {dest}")

    if sys.platform in ("darwin", "ios"):
        # Read the install_name (LC_ID_DYLIB) from the copied dylib
        try:
            out = subprocess.check_output(
                ["otool", "-D", str(dest)], text=True
            ).strip().splitlines()
            if len(out) >= 2:
                old_id = out[1].strip()
                # If install name is @rpath/libthorvg-1.1.dylib but the
                # file is libthorvg-1.dylib, create a symlink from the
                # versioned name so the loader can resolve it.
                id_basename = os.path.basename(old_id)
                if id_basename != src_path.name:
                    versioned_dest = dest_dir / id_basename
                    shutil.copy2(str(dest), str(versioned_dest))
                    print(f"[setup.py] Created versioned copy: {id_basename}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass


# ---------------------------------------------------------------------------
#  Build the Extension kwargs per platform
#
#  All extensions link against the same shared libthorvg-1.  The shared lib
#  is copied into the package source directory so setuptools bundles it in
#  the wheel.  rpath is set to @loader_path (macOS/iOS) or $ORIGIN (Linux)
#  so the extensions find the bundled dylib at runtime.
# ---------------------------------------------------------------------------
include_dirs = [
    THORVG_INCLUDE,
    THORVG_CAPI_INCLUDE,
    str(HERE / "src" / "thorvg_cython"),
]

extra_compile_args = ["-std=c++17"]
extra_link_args = []
libraries = []
library_dirs = []

if _is_ios_build():
    # -----------------------------------------------------------------------
    #  iOS: link against the thorvg dynamic framework from the XCFramework.
    #
    #  At runtime the dylib lives at:
    #    App.app/Frameworks/thorvg.framework/thorvg
    #  with install name @rpath/thorvg.framework/thorvg.
    #  Xcode sets LD_RUNPATH_SEARCH_PATHS = @executable_path/Frameworks
    #  so extensions find it via @rpath.
    #
    #  The dylib is NOT bundled in the wheel — it ships via the .xcframework
    #  embedded in the Xcode project.
    # -----------------------------------------------------------------------
    arch = _get_arch()
    xcfw = Path(THORVG_XCFRAMEWORK)

    _is_simulator = False
    try:
        from platform import ios_ver
        _is_simulator = ios_ver().is_simulator
    except (ImportError, AttributeError):
        pass
    if not _is_simulator:
        _soabi = sysconfig.get_config_var("SOABI") or ""
        _multiarch = sysconfig.get_config_var("MULTIARCH") or ""
        if "simulator" in _soabi or "simulator" in _multiarch:
            _is_simulator = True
    if not _is_simulator:
        if "simulator" in _xcode_platform.lower() or "simulator" in _host_platform.lower():
            _is_simulator = True

    # Locate the framework inside the xcframework
    _ios_fw_dylib = None
    _ios_fw_dir = None

    # Try THORVG_LIB_DIR first (direct build output with framework).
    # Only for device builds — THORVG_LIB_DIR typically points to the
    # device (arm64) output and would be the wrong architecture for
    # simulator (x86_64) builds.
    if not _is_simulator:
        _direct_fw = Path(THORVG_LIB_DIR) / "thorvg.framework" / "thorvg"
        if _direct_fw.exists():
            _ios_fw_dylib = _direct_fw
            _ios_fw_dir = _direct_fw.parent

    if not _ios_fw_dylib:
        # Search xcframework slices
        if _is_simulator:
            slice_candidates = [
                xcfw / "ios-arm64_x86_64-simulator",
                xcfw / f"ios-{arch}-simulator",
            ]
        else:
            slice_candidates = [xcfw / "ios-arm64", xcfw / f"ios-{arch}"]
        for c in slice_candidates:
            fw = c / "thorvg.framework" / "thorvg"
            if fw.exists():
                _ios_fw_dylib = fw
                _ios_fw_dir = fw.parent
                break

    if _ios_fw_dylib:
        # -F for framework search, -framework to link
        library_dirs.append(str(_ios_fw_dir.parent))  # dir containing thorvg.framework/
        extra_link_args.extend([
            f"-F{_ios_fw_dir.parent}",
            "-framework", "thorvg",
        ])
        # Runtime: @rpath = @executable_path/Frameworks (set by Xcode)
        extra_link_args.append("-Wl,-rpath,@executable_path/Frameworks")
        print(f"[setup.py] iOS: linking against {_ios_fw_dylib}")
        print(f"[setup.py] iOS: runtime load path = @rpath/thorvg.framework/thorvg")
    else:
        # Fallback: try bare dylib (legacy / direct meson build)
        _ios_lib_dir = Path(THORVG_LIB_DIR)
        _ios_dylib = _ios_lib_dir / "libthorvg-1.dylib"
        if _ios_dylib.exists():
            library_dirs.append(str(_ios_lib_dir))
            libraries.append("thorvg-1")
            extra_link_args.append("-Wl,-rpath,@executable_path/Frameworks")
            print(f"[setup.py] iOS: fallback linking against {_ios_dylib}")
        else:
            print(f"[setup.py] WARNING: no thorvg dylib/framework found for iOS!")
            libraries.append("thorvg")

    # --- libomp framework (thorvg dynamically links libomp on iOS) ---
    _omp_xcfw = Path(LIBOMP_XCFRAMEWORK)
    _omp_fw_dylib = None
    _omp_fw_dir = None

    if _omp_xcfw.is_dir():
        if _is_simulator:
            _omp_slice_candidates = [
                _omp_xcfw / "ios-arm64_x86_64-simulator",
                _omp_xcfw / f"ios-{arch}-simulator",
            ]
        else:
            _omp_slice_candidates = [_omp_xcfw / "ios-arm64", _omp_xcfw / f"ios-{arch}"]
        for _oc in _omp_slice_candidates:
            _ofw = _oc / "libomp.framework" / "libomp"
            if _ofw.exists():
                _omp_fw_dylib = _ofw
                _omp_fw_dir = _ofw.parent
                break

    if _omp_fw_dylib:
        extra_link_args.extend([
            f"-F{_omp_fw_dir.parent}",
            "-framework", "libomp",
        ])
        print(f"[setup.py] iOS: linking against {_omp_fw_dylib}")
    else:
        print(f"[setup.py] iOS: libomp.xcframework not found at {_omp_xcfw}, skipping")

    extra_link_args.extend(["-framework", "Foundation", "-framework", "CoreGraphics"])
    ios_target = os.environ.get("IPHONEOS_DEPLOYMENT_TARGET", "13.0")
    extra_compile_args.append(f"-mios-version-min={ios_target}")
    extra_link_args.append(f"-mios-version-min={ios_target}")

elif _is_macos_build():
    # -----------------------------------------------------------------------
    #  macOS: link against libthorvg-1.dylib.
    #
    #  Search order:
    #    1. THORVG_LIB_DIR / libthorvg-1.dylib
    #    2. XCFramework macOS slice
    #    3. Fallback: system search
    # -----------------------------------------------------------------------
    xcfw = Path(THORVG_XCFRAMEWORK)
    _lib_dir = Path(THORVG_LIB_DIR)

    local_dylib = _lib_dir / "libthorvg-1.dylib"
    macos_slice = xcfw / "macos-arm64_x86_64"
    macos_dylib = macos_slice / "libthorvg-1.dylib"

    if local_dylib.exists():
        _found_dylib = local_dylib
        _found_dir = _lib_dir
    elif macos_dylib.exists():
        _found_dylib = macos_dylib
        _found_dir = macos_slice
    else:
        _found_dylib = None
        _found_dir = None

    if _found_dylib:
        _bundle_dylib(_found_dylib, _PKG_SRC)
        library_dirs.append(str(_found_dir))
        libraries.append("thorvg-1")
        extra_link_args.append("-Wl,-rpath,@loader_path")
    else:
        libraries.append("thorvg")

    macos_target = os.environ.get("MACOSX_DEPLOYMENT_TARGET", "11.0")
    extra_compile_args.append(f"-mmacosx-version-min={macos_target}")
    extra_link_args.append(f"-mmacosx-version-min={macos_target}")

    # ANGLE dylibs (for GPU builds)
    _angle_dir = Path(ANGLE_LIB_DIR)
    _angle_egl = _angle_dir / "libEGL.dylib"
    _angle_gles = _angle_dir / "libGLESv2.dylib"
    if _angle_egl.exists() and _angle_gles.exists():
        for dylib in (_angle_egl, _angle_gles):
            _dest = _PKG_SRC / dylib.name
            if not _dest.exists():
                shutil.copy2(str(dylib), str(_dest))
                print(f"[setup.py] Copied ANGLE dylib: {dylib.name} -> {_dest}")
        print(f"[setup.py] ANGLE dylibs found, @loader_path rpath already set")

elif sys.platform.startswith("win"):
    # -----------------------------------------------------------------------
    #  Windows: link against thorvg-1.dll via import lib.
    #
    #  Search order:
    #    1. THORVG_LIB_DIR / windows_{arch} / thorvg-1.dll
    #    2. THORVG_LIB_DIR / thorvg-1.dll  (flat layout)
    #    3. output/windows_{arch}/
    #    4. Fallback: linker search
    #
    #  Arch detection: cibuildwheel for Windows ARM64 cross-compilation
    #  uses a host x64 Python, so sysconfig.get_platform() may return
    #  "win-amd64" even when targeting arm64.  We check multiple sources:
    #    - _PYTHON_HOST_PLATFORM  (Python 3.12+ cross-compile)
    #    - SETUPTOOLS_EXT_SUFFIX  (cibuildwheel sets e.g. .cp311-win_arm64.pyd)
    #    - VSCMD_ARG_TGT_ARCH    (Visual Studio dev env)
    #    - sysconfig.get_platform()
    # -----------------------------------------------------------------------
    _host_plat = os.environ.get("_PYTHON_HOST_PLATFORM", "") or sysconfig.get_platform()
    _ext_suffix = os.environ.get("SETUPTOOLS_EXT_SUFFIX", "")
    _vscmd_arch = os.environ.get("VSCMD_ARG_TGT_ARCH", "")
    if "arm64" in _host_plat or "arm64" in _ext_suffix or _vscmd_arch.lower() == "arm64":
        _win_arch = "arm64"
    else:
        _win_arch = "x64"
    print(f"[setup.py] Windows arch={_win_arch}, _host_plat={_host_plat!r}, "
          f"SETUPTOOLS_EXT_SUFFIX={_ext_suffix!r}, VSCMD_ARG_TGT_ARCH={_vscmd_arch!r}")

    _lib_dir = Path(THORVG_LIB_DIR)
    _win_arch_dir = _lib_dir / f"windows_{_win_arch}"
    _win_dll_arch = _win_arch_dir / "thorvg-1.dll"
    _win_dll_flat = _lib_dir / "thorvg-1.dll"
    _win_default_dir = THORVG_ROOT / "output" / f"windows_{_win_arch}"

    if _win_dll_arch.exists():
        _found_dir = _win_arch_dir
    elif _win_dll_flat.exists():
        _found_dir = _lib_dir
    elif (_win_default_dir / "thorvg-1.dll").exists():
        _found_dir = _win_default_dir
    else:
        _found_dir = None

    if _found_dir:
        _bundle_dylib(_found_dir / "thorvg-1.dll", _PKG_SRC)
        library_dirs.append(str(_found_dir))
        libraries.append("thorvg-1")
    else:
        library_dirs.append(THORVG_LIB_DIR)
        libraries.append("thorvg")

    extra_compile_args = ["/std:c++17", "/EHsc"]

elif _is_android_build():
    # -----------------------------------------------------------------------
    #  Android: link against libthorvg-1.so.
    # -----------------------------------------------------------------------
    _android_arch = "aarch64"
    _host_plat = os.environ.get("_PYTHON_HOST_PLATFORM", "") or sysconfig.get_platform()
    if "x86_64" in _host_plat:
        _android_arch = "x86_64"
    elif "aarch64" in _host_plat or "arm64" in _host_plat:
        _android_arch = "aarch64"

    _lib_dir = Path(THORVG_LIB_DIR) / f"android_{_android_arch}"
    if not _lib_dir.exists():
        _lib_dir = Path(THORVG_LIB_DIR)

    _android_so = _lib_dir / "libthorvg-1.so"
    print(f"[setup.py] Android arch={_android_arch}, _host_plat={_host_plat!r}, lib_dir={_lib_dir}")

    if _android_so.exists():
        # Do NOT copy into the package dir — libthorvg-1.so is injected into
        # .libs/{abi}/ in the wheel by tools/add_android_libs.py (repair step).
        # Gradle picks it up from .libs/{abi}/ and places it in the APK's
        # lib/{abi}/, where Android's linker resolves it at runtime.
        library_dirs.append(str(_lib_dir))
        libraries.append("thorvg-1")
    else:
        library_dirs.append(str(_lib_dir))
        libraries.append("thorvg")

else:
    # -----------------------------------------------------------------------
    #  Linux / other: link against libthorvg-1.so.
    #
    #  Arch detection mirrors Android/Windows: when THORVG_LIB_DIR points
    #  to throvg/output (parent), we look in linux_{arch}/ subdirectory.
    # -----------------------------------------------------------------------
    import platform as _plat_mod
    _host_plat = os.environ.get("_PYTHON_HOST_PLATFORM", "") or sysconfig.get_platform()
    if "aarch64" in _host_plat or "arm64" in _host_plat:
        _linux_arch = "aarch64"
    elif "x86_64" in _host_plat:
        _linux_arch = "x86_64"
    else:
        _linux_arch = _plat_mod.machine()
    print(f"[setup.py] Linux arch={_linux_arch}, _host_plat={_host_plat!r}")

    _lib_dir = Path(THORVG_LIB_DIR)
    _linux_arch_dir = _lib_dir / f"linux_{_linux_arch}"
    if _linux_arch_dir.exists():
        _lib_dir = _linux_arch_dir

    _linux_so = _lib_dir / "libthorvg-1.so"

    if _linux_so.exists():
        _bundle_dylib(_linux_so, _PKG_SRC)
        library_dirs.append(str(_lib_dir))
        libraries.append("thorvg-1")
        extra_link_args.append("-Wl,-rpath,$ORIGIN")
    else:
        library_dirs.append(THORVG_LIB_DIR)
        libraries.append("thorvg")
        extra_link_args.append(f"-Wl,-rpath,{THORVG_LIB_DIR}")

# C++ standard library linking
if sys.platform in ("darwin", "ios"):
    extra_link_args.append("-lc++")
elif _is_android_build():
    # Statically link libc++ so extensions don't have DT_NEEDED: libc++_shared.so
    extra_link_args.append("-static-libstdc++")

# ---------------------------------------------------------------------------
#  Extension definition — all extensions share the same link kwargs
# ---------------------------------------------------------------------------
print(f"[setup.py] libraries={libraries}, library_dirs={library_dirs}")
print(f"[setup.py] extra_link_args={extra_link_args}")

_ext_kwargs = dict(
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language="c++",
)

_ext_modules = [
    Extension(
        name="thorvg_cython.thorvg",
        sources=["src/thorvg_cython/thorvg.pyx"],
        **_ext_kwargs,
    ),
    Extension(
        name="thorvg_cython.sw_canvas",
        sources=["src/thorvg_cython/sw_canvas.pyx"],
        **_ext_kwargs,
    ),
]

if GL_MODE:
    _ext_modules.append(
        Extension(
            name="thorvg_cython.gl_canvas",
            sources=["src/thorvg_cython/gl_canvas.pyx"],
            **_ext_kwargs,
        ),
    )
    print(f"[setup.py] GL_MODE enabled (THORVG_GPU={THORVG_GPU!r}) -- compiling GlCanvas")
elif VULKAN_MODE:
    _ext_modules.append(
        Extension(
            name="thorvg_cython.vulkan_canvas",
            sources=["src/thorvg_cython/vulkan_canvas.pyx"],
            **_ext_kwargs,
        ),
    )
    print(f"[setup.py] VULKAN_MODE enabled -- compiling VulkanCanvas")
else:
    print("[setup.py] GPU_MODE disabled -- gl_canvas.py and vulkan_canvas.py stubs will be used")

extensions = cythonize(
    _ext_modules,
    compiler_directives={
        "language_level": "3",
        "boundscheck": False,
        "wraparound": False,
    },
)

# ---------------------------------------------------------------------------
#  Setup
# ---------------------------------------------------------------------------
_thorvg_cython_exclude = []
if GL_MODE:
    _thorvg_cython_exclude.append("gl_canvas.py")
if VULKAN_MODE:
    _thorvg_cython_exclude.append("vulkan_canvas.py")
if _is_ios_build():
    # iOS links thorvg/libomp/wgpu via their .xcframeworks (injected into
    # .frameworks/ post-build by tools/add-ios-frameworks.py). Bare .dylibs
    # only belong in this package dir for macOS (@loader_path linking) — if a
    # prior macOS build left one in src/thorvg_cython/, the unscoped
    # package_data glob below would sweep it into the iOS wheel too.
    _thorvg_cython_exclude.append("*.dylib")

setup(
    name="thorvg-cython",
    version="1.0.0",
    description="Cython bindings for the ThorVG vector graphics library",
    long_description=(HERE / "README.md").read_text(encoding="utf-8")
        if (HERE / "README.md").exists() else "",
    long_description_content_type="text/markdown",
    author="ThorVG",
    license="MIT",
    url="https://github.com/thorvg/thorvg",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    exclude_package_data={
        "": ["*.cpp"],
        **({"thorvg_cython": _thorvg_cython_exclude} if _thorvg_cython_exclude else {}),
    },
    package_data={"thorvg_cython": ["*.dylib", "*.so", "*.dll", "*.pxd", "*.pyi"]},
    ext_modules=extensions,
    python_requires=">=3.9",
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS",
        "Operating System :: iOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Multimedia :: Graphics",
    ],
)
