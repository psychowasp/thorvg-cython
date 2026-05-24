# Canvas

Canvases are the render targets where paints are drawn. thorvg-cython provides two canvas types:

- **`SwCanvas`** — Software rasterization (CPU), with a built-in pixel buffer
- **`GlCanvas`** — Hardware-accelerated OpenGL rendering (GPU)

## Canvas (Base Class)

All canvas types inherit from `Canvas` and share these methods:

### `add(paint)`

```python
def add(self, paint: Paint) -> Result
```

Add a paint to the canvas's drawing list. The paint will be rendered on the next `draw()` call.

### `insert(target, at=None)`

```python
def insert(self, target: Paint, at: Paint | None = None) -> Result
```

Insert a paint at a specific position in the draw list. If `at` is `None`, inserts at the beginning.

### `remove(paint=None)`

```python
def remove(self, paint: Paint | None = None) -> Result
```

Remove a paint from the canvas. If `paint` is `None`, removes all paints.

### `update()`

```python
def update(self) -> Result
```

Notify the canvas that paints have been modified. Call this before `draw()` if you've changed any paint properties after the initial `add()`.

### `draw(clear=True)`

```python
def draw(self, clear: bool = True) -> Result
```

Rasterize all paints. If `clear` is `True`, the canvas is cleared before drawing.

### `sync()`

```python
def sync(self) -> Result
```

Wait for rendering to complete. After `sync()`, the pixel buffer (SwCanvas) or framebuffer (GlCanvas) contains the final image.

### `set_viewport(x, y, w, h)`

```python
def set_viewport(self, x: int, y: int, w: int, h: int) -> Result
```

Set the visible viewport region. Only content within this rectangle will be rendered.

### `destroy()`

```python
def destroy(self) -> Result
```

Explicitly destroy the canvas and release GPU/CPU resources.

---

## SwCanvas

Software-rasterized canvas with an integrated pixel buffer supporting the Python buffer protocol (PEP 3118).

### Constructor

```python
SwCanvas(w=0, h=0, cs=0, engine_option=1)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `w` | `int` | `0` | Width in pixels |
| `h` | `int` | `0` | Height in pixels |
| `cs` | `int` | `0` | Colorspace (see `Colorspace` enum) |
| `engine_option` | `int` | `1` | Engine quality option |

```python
canvas = tvg.SwCanvas(800, 600)
```

### `resize(w, h, cs=-1)`

```python
def resize(self, w: int, h: int, cs: int = -1) -> Result
```

Resize the internal pixel buffer. If `cs` is -1, keeps the current colorspace.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `width` | `int` | Buffer width in pixels |
| `height` | `int` | Buffer height in pixels |
| `colorspace` | `Colorspace` | Pixel format |
| `buffer` | `PixelBuffer | None` | The internal pixel buffer |

### `clear()`

```python
def clear(self) -> None
```

Zero out all pixels in the buffer.

### Buffer Protocol

`SwCanvas` implements PEP 3118 — you can use it directly wherever a buffer is expected:

```python
# As bytes
raw = bytes(canvas)

# As memoryview
mv = memoryview(canvas)

# With NumPy (zero-copy)
import numpy as np
arr = np.frombuffer(canvas, dtype=np.uint8).reshape(h, w, 4)

# With Kivy textures (zero-copy blit)
texture.blit_buffer(canvas, colorfmt='rgba', bufferfmt='ubyte')
```

---

## GlCanvas

OpenGL-accelerated canvas for GPU rendering. Unlike `SwCanvas`, it does not manage a pixel buffer — you provide an active OpenGL context.

### Constructor

```python
GlCanvas(engine_option=1)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `engine_option` | `int` | `1` | Engine quality option |

### `target(display, surface, context, fbo_id, w, h, cs=0)`

```python
def target(
    self,
    display: int,   # EGLDisplay (0 for no EGL management)
    surface: int,   # EGLSurface (0 for no EGL management)
    context: int,   # GL context handle (0 = caller manages)
    fbo_id: int,    # FBO ID (0 = default framebuffer)
    w: int,         # Render width
    h: int,         # Render height
    cs: int = 0,    # Colorspace
) -> Result
```

Set the OpenGL render target.

```python
canvas = tvg.GlCanvas()
canvas.target(0, 0, 0, fbo_id, 1280, 720)
```

!!! note "Platform Notes"
    - **macOS/iOS**: Uses ANGLE (OpenGL ES → Metal). Ensure `libEGL.dylib` and `libGLESv2.dylib` are loadable.
    - **Linux/Windows**: Uses native OpenGL.
    - **Android**: Uses native OpenGL ES.

---

## Render Pipeline

The typical render loop:

```python
# Initial render
canvas.add(shape)
canvas.draw()
canvas.sync()

# After modifying paints:
shape.translate(10, 0)
canvas.update()
canvas.draw()
canvas.sync()
```

!!! tip "Smart Render"
    Use `EngineOption.SMART_RENDER` to enable incremental rendering — only modified regions are redrawn:

    ```python
    canvas = tvg.SwCanvas(800, 600, engine_option=tvg.EngineOption.SMART_RENDER)
    ```
