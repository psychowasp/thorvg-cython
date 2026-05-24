# thorvg-cython

**High-performance Cython bindings for the [ThorVG](https://www.thorvg.org) vector graphics library.**

---

## What is thorvg-cython?

thorvg-cython provides **direct C-level bindings** to [ThorVG](https://github.com/thorvg/thorvg) via Cython — no ctypes overhead. It delivers native-extension performance for vector graphics rendering in Python, with support for:

- **SVG rendering** — Load and render SVG files and inline SVG data
- **Lottie animations** — Play back Lottie JSON animations at full frame rate
- **Shape primitives** — Rectangles, circles, paths, strokes, and fills
- **GPU acceleration** — OpenGL-based rendering via `GlCanvas`
- **Zero-copy buffer protocol** — PEP 3118 compliant for direct integration with Kivy, NumPy, and more
- **Cross-platform** — Linux, macOS, Windows, iOS, and Android

## Quick Example

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2) as engine:
    canvas = tvg.SwCanvas(800, 600)

    # Draw a red rounded rectangle
    shape = tvg.Shape()
    shape.append_rect(50, 50, 200, 150, rx=20, ry=20)
    shape.set_fill_color(255, 0, 0)
    canvas.add(shape)

    canvas.draw()
    canvas.sync()

    # Get raw RGBA pixels — zero copy!
    raw = bytes(canvas)
```

## GPU Rendering

```python
import thorvg_cython as tvg

tvg.Engine(threads=4)

canvas = tvg.GlCanvas()
# Bind to your existing OpenGL context/FBO
canvas.target(0, 0, 0, fbo_id, width, height)

shape = tvg.Shape()
shape.append_circle(400, 300, 100, 100)
shape.set_fill_color(0, 200, 255)
canvas.add(shape)

canvas.draw()
canvas.sync()
```

## Platform Support

| Platform | Status |
|----------|--------|
| **Linux** (x86_64, aarch64) | ✅ Fully supported |
| **macOS** (x86_64, arm64) | ✅ Fully supported |
| **Windows** (x86_64) | ✅ Fully supported |
| **iOS** (arm64) | ✅ Fully supported |
| **Android** (arm64, x86_64) | ✅ Fully supported |

## Next Steps

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Get up and running in minutes with pip or from source.

    [:octicons-arrow-right-24: Install](getting-started/installation.md)

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Learn the basics with hands-on examples.

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **API Reference**

    ---

    Complete reference for all classes and methods.

    [:octicons-arrow-right-24: API Reference](api/overview.md)

-   :material-gpu:{ .lg .middle } **GPU Rendering**

    ---

    Hardware-accelerated rendering with GlCanvas.

    [:octicons-arrow-right-24: GPU Guide](guides/gpu-rendering.md)

</div>
