# Utilities

## Saver

Export paints and animations to files (TVG, GIF).

### Constructor

```python
saver = tvg.Saver()
```

### `save_paint(paint, path, quality=100)`
```python
def save_paint(self, paint: Paint, path: str, quality: int = 100) -> Result
```
Save a paint to a file. The format is determined by the file extension.

### `save_animation(animation, path, quality=100, fps=0)`
```python
def save_animation(self, animation: Animation, path: str,
                   quality: int = 100, fps: int = 0) -> Result
```
Save an animation to a file (e.g., GIF).

### `sync()`
```python
def sync(self) -> Result
```
Wait for the save operation to complete.

### Example

```python
import thorvg_cython as tvg

with tvg.Engine():
    shape = tvg.Shape()
    shape.append_circle(100, 100, 80, 80)
    shape.set_fill_color(255, 100, 50)

    saver = tvg.Saver()
    saver.save_paint(shape, "circle.tvg")
    saver.sync()
```

---

## Accessor

Utility for generating unique IDs from string names.

### Constructor

```python
accessor = tvg.Accessor()
```

### `Accessor.generate_id(name)` (static)
```python
@staticmethod
def generate_id(name: str) -> int
```
Generate a deterministic numeric ID from a string name.

```python
id = tvg.Accessor.generate_id("my_layer")
```

---

## PixelBuffer

Heap-allocated RGBA pixel buffer that implements the Python buffer protocol (PEP 3118).

### Constructor

```python
buf = tvg.PixelBuffer(w, h, cs=0, stride=0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `w` | `int` | — | Width in pixels |
| `h` | `int` | — | Height in pixels |
| `cs` | `int` | `0` | Colorspace |
| `stride` | `int` | `0` | Row stride (0 = same as width) |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `width` | `int` | Buffer width |
| `height` | `int` | Buffer height |
| `stride` | `int` | Row stride in pixels |
| `colorspace` | `Colorspace` | Pixel format |
| `nbytes` | `int` | Total buffer size in bytes |
| `ptr` | `int` | Raw memory address (for C interop) |

### `clear()`
```python
def clear(self) -> None
```
Zero all pixels.

### Buffer Protocol

`PixelBuffer` supports PEP 3118. Use it anywhere Python expects a buffer:

```python
buf = tvg.PixelBuffer(256, 256)

# As bytes
data = bytes(buf)

# As memoryview
mv = memoryview(buf)

# With NumPy
import numpy as np
arr = np.frombuffer(buf, dtype=np.uint8).reshape(256, 256, 4)

# With Kivy
texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
```
