# GPU Rendering with GlCanvas

thorvg-cython supports hardware-accelerated rendering through `GlCanvas`, which uses OpenGL (or OpenGL ES via ANGLE on Apple platforms) to rasterize vector graphics on the GPU.

## When to Use GPU Rendering

| Use Case | Recommended Canvas |
|----------|-------------------|
| Static SVG/image rendering | `SwCanvas` |
| Simple UI with few redraws | `SwCanvas` |
| Real-time games (60fps) | `GlCanvas` ✨ |
| Complex scenes with many shapes | `GlCanvas` ✨ |
| Animated content with transforms | `GlCanvas` ✨ |
| Headless rendering / export | `SwCanvas` |

## Basic Setup

```python
import thorvg_cython as tvg

# Initialize engine
tvg.Engine(threads=4)

# Create GL canvas
canvas = tvg.GlCanvas()

# Bind to your GL context's framebuffer
# Parameters: display, surface, context, fbo_id, width, height
canvas.target(0, 0, 0, fbo_id, 1280, 720)
```

!!! info "Context Management"
    When you pass `0` for display, surface, and context, thorvg assumes the GL context is already current. **You** must ensure an active OpenGL context before calling `target()`.

## Platform Setup

=== "Kivy (All Platforms)"

    Kivy manages the OpenGL context for you. Access the FBO from a Kivy `Fbo` or `RenderContext`:

    ```python
    from kivy.graphics import Fbo, Rectangle
    from kivy.graphics.opengl import glGetIntegerv, GL_FRAMEBUFFER_BINDING
    import thorvg_cython as tvg

    tvg.Engine(threads=4)

    class GpuWidget(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._canvas_tvg = tvg.GlCanvas()

        def on_size(self, *args):
            w, h = int(self.width), int(self.height)
            # Get the current FBO that Kivy is rendering to
            fbo_id = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
            self._canvas_tvg.target(0, 0, 0, fbo_id, w, h)
    ```

=== "GLFW (Desktop)"

    ```python
    import glfw
    import thorvg_cython as tvg

    glfw.init()
    window = glfw.create_window(1280, 720, "ThorVG GPU", None, None)
    glfw.make_context_current(window)

    tvg.Engine(threads=4)
    canvas = tvg.GlCanvas()
    canvas.target(0, 0, 0, 0, 1280, 720)  # FBO 0 = default framebuffer
    ```

=== "macOS / iOS (ANGLE)"

    On Apple platforms, ThorVG uses ANGLE to translate OpenGL ES calls to Metal:

    ```python
    import thorvg_cython as tvg

    # Ensure ANGLE dylibs are in your library path:
    #   libEGL.dylib, libGLESv2.dylib

    tvg.Engine(threads=4)
    canvas = tvg.GlCanvas()

    # Pass EGL handles if managing context yourself,
    # or 0 to let the caller handle context binding
    canvas.target(egl_display, egl_surface, egl_context, 0, w, h)
    ```

## Render Loop

The GPU render loop is similar to software rendering:

```python
# Setup
canvas = tvg.GlCanvas()
canvas.target(0, 0, 0, fbo_id, width, height)

# Build scene (once)
root = tvg.Scene()
canvas.add(root)

shape = tvg.Shape()
shape.append_circle(400, 300, 100, 100)
shape.set_fill_color(0, 200, 255)
root.add(shape)

# Each frame:
def render_frame(dt):
    # Update transforms
    shape.translate(dx, dy)

    # Render
    canvas.update()
    canvas.draw()
    canvas.sync()
```

## GPU Game Architecture

For games, use a scene graph with separate layers:

```python
import thorvg_cython as tvg

class Game:
    def __init__(self, canvas: tvg.GlCanvas, w: float, h: float):
        self.canvas = canvas

        # Layer hierarchy
        self._root = tvg.Scene()
        canvas.add(self._root)

        # Background layer
        self._bg = tvg.Shape()
        self._bg.append_rect(0, 0, w, h)
        self._bg.set_fill_color(10, 10, 20)
        self._root.add(self._bg)

        # Game objects layer
        self._game_scene = tvg.Scene()
        self._root.add(self._game_scene)

        # HUD layer (always on top)
        self._hud_scene = tvg.Scene()
        canvas.add(self._hud_scene)

    def tick(self, dt: float):
        # Update game logic, move shapes...
        self._update_objects(dt)

        # Render
        self.canvas.update()
        self.canvas.draw()
        self.canvas.sync()
```

## Transforms with Matrix

For games and animations, direct matrix manipulation is key for GPU-rendered shapes:

```python
import math
import thorvg_cython as tvg

# Rotate a shape around a point
def set_position_rotation(shape, x, y, angle_rad):
    m = tvg.Matrix()
    m.e11 = math.cos(angle_rad)
    m.e12 = -math.sin(angle_rad)
    m.e21 = math.sin(angle_rad)
    m.e22 = math.cos(angle_rad)
    m.e13 = x  # translate X
    m.e23 = y  # translate Y
    shape.set_transform(m)

# Usage in game loop
set_position_rotation(player_shape, player_x, player_y, player_angle)
```

## Neon Vector Style (Game Art)

The [kivy-thor-games](https://github.com/Py-Swift/kivy-thor-games) project demonstrates a "neon vector" art style using layered strokes:

```python
def draw_neon_shape(scene, path_fn, size, color):
    """Create a neon-glowing vector shape using bloom layers."""
    r, g, b = color

    # Bloom layer (wide, faint)
    bloom = tvg.Shape()
    path_fn(bloom, size)
    bloom.set_stroke_width(12.0)
    bloom.set_stroke_color(r, g, b, 38)
    bloom.set_stroke_join(tvg.StrokeJoin.ROUND)
    scene.add(bloom)

    # Fill layer (semi-transparent)
    fill = tvg.Shape()
    path_fn(fill, size)
    fill.set_fill_color(r, g, b, 76)
    scene.add(fill)

    # Glow layer (medium stroke)
    glow = tvg.Shape()
    path_fn(glow, size)
    glow.set_stroke_width(5.0)
    glow.set_stroke_color(r, g, b, 178)
    glow.set_stroke_join(tvg.StrokeJoin.ROUND)
    scene.add(glow)

    # Core layer (thin, bright)
    core = tvg.Shape()
    path_fn(core, size)
    core.set_stroke_width(2.0)
    core.set_stroke_color(r, g, b, 255)
    core.set_stroke_join(tvg.StrokeJoin.ROUND)
    scene.add(core)

    return bloom, fill, glow, core
```

## Resize Handling

When the window resizes, update the GL target:

```python
def on_resize(new_w, new_h):
    canvas.target(0, 0, 0, fbo_id, new_w, new_h)
    # Rebuild background and adjust layout
    bg.reset()
    bg.append_rect(0, 0, new_w, new_h)
    bg.set_fill_color(10, 10, 20)
```

## Performance Tips

1. **Minimize shape rebuilds** — Use `set_transform()` instead of `reset()` + rebuild for moving objects
2. **Use scenes** — Group static objects in a scene so they're updated together
3. **Batch similar objects** — Objects with the same visual style render more efficiently together
4. **Use `draw(clear=True)`** — Lets the GPU optimize buffer management
5. **Set viewport** — Use `canvas.set_viewport()` to limit rendering to visible area
