---
hide:
  - navigation
  - toc
---

# thorvg-cython

<div class="hero" markdown>

**High-performance Cython bindings for the [ThorVG](https://www.thorvg.org) vector graphics library.**{ .hero-tagline }

[:material-download: Install](getting-started/installation.md){ .md-button .md-button--primary }
[:material-rocket-launch: Quick Start](getting-started/quickstart.md){ .md-button }

</div>

---

## Why thorvg-cython?

thorvg-cython provides **direct C-level bindings** to [ThorVG](https://github.com/thorvg/thorvg) via Cython — no ctypes overhead, no FFI marshalling. It delivers native-extension performance for vector graphics rendering in Python.

<div class="grid cards" markdown>

-   :material-svg:{ .lg .middle } **SVG Rendering**

    ---

    Load and render SVG files and inline SVG data at native speed with full feature support.

-   :material-animation-play:{ .lg .middle } **Lottie Animations**

    ---

    Play back Lottie JSON animations at full frame rate with segment, marker, and tween control.

-   :material-shape:{ .lg .middle } **Shape Primitives**

    ---

    Rectangles, circles, paths, Bézier curves, strokes, fills, and gradients — all hardware-accelerated.

-   :material-chip:{ .lg .middle } **GPU Acceleration**

    ---

    OpenGL-based rendering via `GlCanvas` for real-time games and complex animated scenes at 60fps.

-   :material-memory:{ .lg .middle } **Zero-Copy Buffer Protocol**

    ---

    PEP 3118 compliant — direct integration with Kivy textures, NumPy arrays, and memoryviews.

-   :material-cellphone-link:{ .lg .middle } **Cross-Platform**

    ---

    Linux, macOS, Windows, iOS, and Android from a single codebase.

</div>

---

## Quick Example

Render a gradient circle and save it as a PNG — in under 15 lines:

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4) as engine:
    canvas = tvg.SwCanvas(800, 600)

    # Draw a radial gradient circle
    circle = tvg.Shape()
    circle.append_circle(400, 300, 150, 150)

    grad = tvg.RadialGradient(400, 300, 150)
    grad.set_color_stops([
        tvg.ColorStop(0.0, 255, 100, 50),
        tvg.ColorStop(1.0, 100, 0, 200),
    ])
    circle.set_gradient(grad)
    canvas.add(circle)

    canvas.draw()
    canvas.sync()

    # Save — zero-copy buffer protocol!
    from PIL import Image
    img = Image.frombytes("RGBA", (800, 600), bytes(canvas))
    img.save("output.png")
```

## GPU Rendering

For real-time applications and games, use `GlCanvas` for hardware-accelerated rendering:

```python
import thorvg_cython as tvg

tvg.Engine(threads=4)

canvas = tvg.GlCanvas()
canvas.target(0, 0, 0, fbo_id, 1280, 720)

# Build a scene
root = tvg.Scene()
canvas.add(root)

shape = tvg.Shape()
shape.append_circle(640, 360, 100, 100)
shape.set_fill_color(0, 200, 255)
root.add(shape)

# Render at 60fps in your game loop
canvas.update()
canvas.draw()
canvas.sync()
```

---

## Platform Support

| Platform | Architectures | Status |
|----------|---------------|--------|
| :fontawesome-brands-linux: **Linux** | x86_64, aarch64 | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-apple: **macOS** | x86_64, arm64 (Apple Silicon) | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-windows: **Windows** | x86_64 | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-apple: **iOS** | arm64 | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-android: **Android** | arm64-v8a, x86_64 | :material-check-circle:{ style="color: #4caf50" } Fully supported |

---

## Explore the Documentation

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Get up and running in minutes with pip or build from source for any platform.

    [:octicons-arrow-right-24: Install thorvg-cython](getting-started/installation.md)

-   :material-rocket-launch:{ .lg .middle } **Quick Start Guide**

    ---

    Learn the core concepts — engine, canvas, paints — with hands-on examples.

    [:octicons-arrow-right-24: Start building](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **API Reference**

    ---

    Complete reference for all classes, methods, properties, and enumerations.

    [:octicons-arrow-right-24: Browse the API](api/overview.md)

-   :material-chip:{ .lg .middle } **GPU Rendering Guide**

    ---

    Hardware-accelerated rendering with GlCanvas for games and real-time apps.

    [:octicons-arrow-right-24: GPU guide](guides/gpu-rendering.md)

-   :material-puzzle:{ .lg .middle } **Kivy Integration**

    ---

    Zero-copy SVG widgets, Lottie players, and GPU rendering inside Kivy apps.

    [:octicons-arrow-right-24: Kivy guide](guides/kivy-integration.md)

-   :material-gamepad-variant:{ .lg .middle } **Game Development**

    ---

    Build neon-vector GPU games with pymunk physics and scene graphs.

    [:octicons-arrow-right-24: Game dev guide](guides/game-development.md)

</div>
