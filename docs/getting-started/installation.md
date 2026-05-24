# Installation

## From PyPI (Recommended)

```bash
pip install thorvg-cython
```

Pre-built wheels are available for:

- Linux (x86_64, aarch64) — Python 3.11–3.14
- macOS (x86_64, arm64) — Python 3.11–3.14
- Windows (x86_64) — Python 3.11–3.14

## From Source

### Prerequisites

- Python ≥ 3.11
- Cython ≥ 3.0
- A C/C++ compiler (gcc, clang, or MSVC)
- ThorVG built with C API bindings (`-Dbindings=capi`)
- Meson & Ninja (for building ThorVG)

### Step 1: Build ThorVG

```bash
# Clone ThorVG
git clone https://github.com/thorvg/thorvg.git
cd thorvg

# Build with the C API enabled
meson setup builddir --buildtype=release \
    --default-library=shared \
    -Dbindings=capi \
    -Dloaders=svg,lottie,ttf \
    -Dengines=cpu,gl
ninja -C builddir
```

!!! tip "Engine Options"
    Use `-Dengines=cpu,gl` to enable both software and OpenGL rendering.
    Valid engine choices in ThorVG v1.0.5+: `cpu`, `gl`, `wg`, `all`.

### Step 2: Build thorvg-cython

```bash
cd thorvg-cython

# Set environment variables pointing to your ThorVG build
export THORVG_ROOT=/path/to/thorvg
export THORVG_LIB_DIR=/path/to/thorvg/builddir/src

# Install in development mode
pip install -e .
```

### Step 3: Verify Installation

```bash
python -c "import thorvg_cython as tvg; print(tvg.__version__)"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `THORVG_ROOT` | Path to ThorVG source root | Parent of this package |
| `THORVG_INCLUDE` | Path to `thorvg.h` | `$THORVG_ROOT/inc` |
| `THORVG_LIB_DIR` | Path to built libraries | `$THORVG_ROOT/output` |
| `THORVG_XCFRAMEWORK` | Path to `.xcframework` (iOS) | `$THORVG_ROOT/output/thorvg.xcframework` |
| `THORVG_CAPI_INCLUDE` | Path to `thorvg_capi.h` | `$THORVG_ROOT/src/bindings/capi` |

## Using the Build Script

The repository includes a build helper that automates ThorVG compilation:

```bash
# Install build dependencies
pip install Cython meson ninja

# Build ThorVG for your platform
python tools/build_thorvg.py linux --thorvg-root=./thorvg --version=1.0.5

# Install with the built library
THORVG_LIB_DIR=thorvg/output/linux_x86_64 pip install -e .
```

=== "Linux"

    ```bash
    python tools/build_thorvg.py linux \
        --thorvg-root=./thorvg --version=1.0.5
    ```

=== "macOS"

    ```bash
    python tools/build_thorvg.py macos \
        --thorvg-root=./thorvg --version=1.0.5
    ```

=== "Windows"

    ```bash
    python tools\build_thorvg.py windows ^
        --thorvg-root=.\thorvg --version=1.0.5
    ```

=== "iOS"

    ```bash
    python tools/build_thorvg.py ios \
        --thorvg-root=./thorvg --version=1.0.5
    ```

=== "Android"

    ```bash
    python tools/build_thorvg.py android \
        --thorvg-root=./thorvg --version=1.0.5
    ```

## Building Wheels with cibuildwheel

```bash
pip install cibuildwheel
cibuildwheel --platform linux  # or macos, windows
```

## Running Tests

```bash
# Set library path so the dynamic library is found
export LD_LIBRARY_PATH=thorvg/output/linux_x86_64

# Run the test suite
pytest tests/ -v
```
