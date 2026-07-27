# thorvg-cython

Cython bindings for the [ThorVG](https://www.thorvg.org) vector graphics library.

## Overview

This package provides **direct C-level bindings** to ThorVG via Cython — no ctypes overhead.
It mirrors the `thorvg-python` API surface while delivering native-extension performance.

## Platform Support

| Platform | Linking Strategy |
|---|---|
| **iOS** (`sys.platform == "ios"`) | Links against `thorvg.xcframework` static slice |
| **macOS** (`sys.platform == "darwin"`) | Links against `libthorvg.a` or `libthorvg-1.dylib` |
| **Linux** | Links against `libthorvg.so` |
| **Windows** | Links against `thorvg.lib` / `thorvg-1.dll` |
| **Android** | Links against `libthorvg.so` |

## Building

### Prerequisites

- Python ≥ 3.9
- Cython ≥ 3.0
- ThorVG built with C API bindings (`-Dbindings=capi`)

### Quick Build (macOS)

```bash
# 1. Build ThorVG
cd /path/to/thorvg
export SDKROOT=$(xcrun --show-sdk-path)
meson setup builddir --buildtype=release --default-library=shared -Dbindings=capi -Dloaders=svg,lottie,ttf
ninja -C builddir

# 2. Build the wheel
cd thorvg-cython
THORVG_ROOT=.. THORVG_LIB_DIR=../builddir/src pip install -e .
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `THORVG_ROOT` | Path to thorvg source root | Parent of this package |
| `THORVG_INCLUDE` | Path to `thorvg.h` | `$THORVG_ROOT/inc` |
| `THORVG_LIB_DIR` | Path to built libraries | `$THORVG_ROOT/output` |
| `THORVG_XCFRAMEWORK` | Path to `.xcframework` | `$THORVG_ROOT/output/thorvg.xcframework` |
| `THORVG_CAPI_INCLUDE` | Path to `thorvg_capi.h` | `$THORVG_ROOT/src/bindings/capi` |
| `NO_EMBED_FRAMEWORKS` | iOS wheel repair only: skip injecting `.frameworks/` (thorvg/libomp/wgpu xcframeworks) into the wheel — for consumers that bundle those frameworks themselves. Extensions are still retargeted to expect `ThorVG.framework`. | unset (frameworks embedded) |

### cibuildwheel

```bash
pip install cibuildwheel
cibuildwheel --platform macos
```

## Usage

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2) as engine:
    canvas = tvg.SwCanvas(800, 600)
    shape = tvg.Shape()
    shape.append_rect(0, 0, 100, 100, rx=10, ry=10)
    shape.set_fill_color(255, 0, 0)
    canvas.add(shape)
    canvas.draw()
    canvas.sync()
```

### Zero-Copy Buffer Protocol (PEP 3118)

`SwCanvas` implements the Python buffer protocol directly — no intermediate
copies needed when passing pixel data to other frameworks.

**Snapshot as `bytes`:**

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(800, 600)

    # Draw a red rounded rectangle
    shape = tvg.Shape()
    shape.append_rect(50, 50, 200, 150, rx=20, ry=20)
    shape.set_fill_color(255, 0, 0)
    canvas.add(shape)

    # Load and render an SVG
    pic = tvg.Picture()
    pic.load("icon.svg")
    pic.set_size(100, 100)
    canvas.add(pic)

    canvas.draw()
    canvas.sync()

    raw = bytes(canvas)  # flat RGBA, 800×600×4 = 1_920_000 bytes
```

**Kivy texture (zero-copy blit):**

```python
from kivy.graphics.texture import Texture
import thorvg_cython as tvg

with tvg.Engine():
    texture = Texture.create(size=(800, 600), colorfmt='rgba')
    canvas = tvg.SwCanvas(800, 600)

    # Load a Lottie animation
    pic = tvg.Picture()
    pic.load("animation.json")
    pic.set_size(800, 600)
    canvas.add(pic)

    # Initial render
    canvas.draw()
    canvas.sync()
    texture.blit_buffer(canvas, colorfmt='rgba', bufferfmt='ubyte')

    # Move the animation and re-render — same canvas, same texture
    pic.translate(100, 50)
    pic.set_opacity(180)
    canvas.update()
    canvas.draw()
    canvas.sync()
    texture.blit_buffer(canvas, colorfmt='rgba', bufferfmt='ubyte')
```

**NumPy array (zero-copy view):**

```python
import numpy as np
import thorvg_cython as tvg

with tvg.Engine():
    canvas = tvg.SwCanvas(400, 300)

    shape = tvg.Shape()
    shape.append_circle(200, 150, 100, 100)
    shape.set_fill_color(0, 120, 255)
    canvas.add(shape)
    canvas.draw()
    canvas.sync()

    # Live view into the canvas pixel buffer — no copy
    arr = np.frombuffer(canvas, dtype=np.uint8).reshape(300, 400, 4)
    arr[:, :, 3] = 128  # set alpha to 50% — modifies canvas directly
```

**`memoryview` (stdlib, zero-copy):**

```python
import thorvg_cython as tvg

with tvg.Engine():
    canvas = tvg.SwCanvas(256, 256)

    shape = tvg.Shape()
    shape.append_rect(0, 0, 256, 256)
    shape.set_fill_color(0, 0, 0)
    canvas.add(shape)
    canvas.draw()
    canvas.sync()

    mv = memoryview(canvas)
    print(len(mv))  # 262_144
    mv[0:4]          # first pixel RGBA bytes
```

## License

MIT — same as ThorVG.
