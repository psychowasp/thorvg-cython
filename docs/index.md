---
hide:
  - navigation
  - toc
---

<div class="hero-section" markdown>

# thorvg-cython

<p class="hero-tagline">
Blazing-fast Cython bindings for <strong>ThorVG</strong> — render SVGs, play Lottie animations, and draw vector graphics at native speed in Python.
</p>

[:material-download: Install](getting-started/installation.md){ .md-button .md-button--primary }
[:material-rocket-launch: Quick Start](getting-started/quickstart.md){ .md-button }
[:fontawesome-brands-github: GitHub](https://github.com/Py-Swift/thorvg-cython){ .md-button }

<div class="hero-stats" markdown>
<div class="stat" markdown>
<span class="stat-value">C-Speed</span>
<span class="stat-label">Native Performance</span>
</div>
<div class="stat" markdown>
<span class="stat-value">5 Platforms</span>
<span class="stat-label">Cross-Platform</span>
</div>
<div class="stat" markdown>
<span class="stat-value">Zero-Copy</span>
<span class="stat-label">Buffer Protocol</span>
</div>
</div>

</div>

<div class="section-header" markdown>

## :material-lightning-bolt: Why thorvg-cython?

Direct C-level bindings via Cython — no ctypes overhead, no FFI marshalling.

</div>

<div class="grid cards" markdown>

-   :material-svg:{ .lg .middle } **SVG Rendering**

    ---

    Load and render SVG files and inline SVG data at native speed with full specification support including gradients, filters, and clip paths.

    [:octicons-arrow-right-24: Learn more](api/picture.md)

-   :material-animation-play:{ .lg .middle } **Lottie Animations**

    ---

    Play Lottie JSON animations at full frame rate with segment control, markers, slot overrides, and frame-accurate tweening.

    [:octicons-arrow-right-24: See examples](examples/lottie-animations.md)

-   :material-shape:{ .lg .middle } **Vector Primitives**

    ---

    Rectangles, circles, Bézier paths, strokes, fills, and linear/radial gradients — all hardware-accelerated.

    [:octicons-arrow-right-24: Shape API](api/shape.md)

-   :material-chip:{ .lg .middle } **GPU Acceleration**

    ---

    OpenGL-based rendering via `GlCanvas` for real-time games, data visualizations, and complex animated scenes at 60fps+.

    [:octicons-arrow-right-24: GPU guide](guides/gpu-rendering.md)

-   :material-memory:{ .lg .middle } **Zero-Copy Buffers**

    ---

    PEP 3118 compliant buffer protocol — direct integration with Kivy textures, NumPy arrays, PIL, and raw memoryviews.

    [:octicons-arrow-right-24: Buffer guide](guides/buffer-protocol.md)

-   :material-cellphone-link:{ .lg .middle } **Cross-Platform**

    ---

    Linux, macOS, Windows, iOS, and Android from a single codebase. Pre-built wheels available for all major platforms.

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

</div>

---

<div class="section-header" markdown>

## :material-code-tags: Quick Example

Render a gradient circle and save as PNG — in under 15 lines.

</div>

=== "CPU Rendering"

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

=== "GPU Rendering"

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

=== "Lottie Animation"

    ```python
    import thorvg_cython as tvg

    with tvg.Engine(threads=4) as engine:
        canvas = tvg.SwCanvas(800, 600)

        # Load and play Lottie animation
        animation = tvg.Animation()
        animation.picture.load("animation.json")
        canvas.add(animation.picture)

        # Seek to specific frame
        total = animation.total_frame
        animation.frame = total * 0.5  # Jump to midpoint

        canvas.update()
        canvas.draw()
        canvas.sync()
    ```

---

<div class="section-header" markdown>

## :material-monitor-multiple: Platform Support

Works everywhere ThorVG runs.

</div>

| Platform | Architectures | Rendering | Status |
|----------|---------------|-----------|--------|
| :fontawesome-brands-linux: **Linux** | x86_64, aarch64 | CPU + GPU | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-apple: **macOS** | x86_64, arm64 (Apple Silicon) | CPU + GPU | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-windows: **Windows** | x86_64 | CPU + GPU | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-apple: **iOS** | arm64 | CPU + GPU | :material-check-circle:{ style="color: #4caf50" } Fully supported |
| :fontawesome-brands-android: **Android** | arm64-v8a, x86_64 | CPU + GPU | :material-check-circle:{ style="color: #4caf50" } Fully supported |

---

<div class="section-header" markdown>

## :material-compass: Explore the Documentation

</div>

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Get up and running in minutes with pip, or build from source for any platform and architecture.

    [:octicons-arrow-right-24: Install thorvg-cython](getting-started/installation.md)

-   :material-rocket-launch:{ .lg .middle } **Quick Start Guide**

    ---

    Learn the core concepts — engine, canvas, paints — with hands-on, copy-paste examples.

    [:octicons-arrow-right-24: Start building](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **API Reference**

    ---

    Complete reference for every class, method, property, and enumeration in the library.

    [:octicons-arrow-right-24: Browse the API](api/overview.md)

-   :material-chip:{ .lg .middle } **GPU Rendering**

    ---

    Hardware-accelerated rendering with GlCanvas for games, visualizations, and real-time apps.

    [:octicons-arrow-right-24: GPU guide](guides/gpu-rendering.md)

-   :material-puzzle:{ .lg .middle } **Kivy Integration**

    ---

    Zero-copy SVG widgets, Lottie animation players, and GPU rendering inside Kivy applications.

    [:octicons-arrow-right-24: Kivy guide](guides/kivy-integration.md)

-   :material-gamepad-variant:{ .lg .middle } **Game Development**

    ---

    Build neon-vector GPU games with pymunk physics, entity-component systems, and scene graphs.

    [:octicons-arrow-right-24: Game dev guide](guides/game-development.md)

</div>
