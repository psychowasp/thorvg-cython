# Buffer Protocol (Zero-Copy)

One of thorvg-cython's key features is its implementation of Python's buffer protocol ([PEP 3118](https://peps.python.org/pep-3118/)). This enables **zero-copy** data sharing with any framework that accepts buffer objects.

## How It Works

Both `SwCanvas` and `PixelBuffer` expose their internal pixel memory directly to Python without copying:

```
┌─────────────────────────┐
│  ThorVG render buffer   │ ← malloc'd RGBA pixels
│  (uint32_t* data)       │
└─────────┬───────────────┘
          │ PEP 3118 buffer protocol
          ▼
┌─────────────────────────┐
│  Python buffer view     │ ← zero-copy access
│  bytes / memoryview /   │
│  numpy / kivy texture   │
└─────────────────────────┘
```

## Usage Patterns

### As `bytes` (snapshot copy)

```python
canvas = tvg.SwCanvas(800, 600)
# ... add paints, draw, sync ...

# Creates a copy — useful for saving/sending
raw = bytes(canvas)  # 800 * 600 * 4 = 1,920,000 bytes
```

### As `memoryview` (zero-copy, stdlib)

```python
canvas = tvg.SwCanvas(256, 256)
# ... render ...

mv = memoryview(canvas)
print(len(mv))       # 262,144 bytes
print(mv[0:4])       # First pixel RGBA
mv[0] = 255          # Modify pixel directly!
```

### With NumPy (zero-copy array view)

```python
import numpy as np

canvas = tvg.SwCanvas(400, 300)
# ... render ...

# Reshape as H×W×4 RGBA array — no copy!
arr = np.frombuffer(canvas, dtype=np.uint8).reshape(300, 400, 4)

# Modify alpha channel directly in the render buffer
arr[:, :, 3] = 128  # 50% opacity

# Analyze pixel data
avg_brightness = arr[:, :, :3].mean()
```

### With Kivy Texture (zero-copy blit)

```python
from kivy.graphics.texture import Texture

canvas = tvg.SwCanvas(800, 600)
# ... render ...

tex = Texture.create(size=(800, 600), colorfmt="rgba")
tex.flip_vertical()

# blit_buffer reads directly from canvas memory — no intermediate copy
tex.blit_buffer(canvas, colorfmt="rgba", bufferfmt="ubyte")
```

### With Pillow (for saving images)

```python
from PIL import Image

canvas = tvg.SwCanvas(800, 600)
# ... render ...

# Pillow does copy the data, but the buffer protocol avoids
# an extra Python-side copy
img = Image.frombytes("RGBA", (800, 600), bytes(canvas))
img.save("output.png")
```

## Re-rendering to the Same Buffer

The buffer stays valid across multiple render cycles:

```python
canvas = tvg.SwCanvas(800, 600)
tex = Texture.create(size=(800, 600), colorfmt="rgba")
tex.flip_vertical()

# Add a shape
shape = tvg.Shape()
shape.append_rect(0, 0, 100, 100)
shape.set_fill_color(255, 0, 0)
canvas.add(shape)

# First render
canvas.draw()
canvas.sync()
tex.blit_buffer(canvas, colorfmt="rgba", bufferfmt="ubyte")

# Modify and re-render — same buffer, same texture
shape.translate(50, 50)
canvas.update()
canvas.draw()
canvas.sync()
tex.blit_buffer(canvas, colorfmt="rgba", bufferfmt="ubyte")
```

## PixelBuffer Standalone

You can use `PixelBuffer` independently:

```python
buf = tvg.PixelBuffer(1024, 768)

# Properties
print(buf.width)       # 1024
print(buf.height)      # 768
print(buf.nbytes)      # 1024 * 768 * 4 = 3,145,728
print(buf.colorspace)  # Colorspace.ABGR8888

# Clear to black
buf.clear()

# Raw pointer (for C/Cython interop)
print(hex(buf.ptr))
```

## Buffer Format Details

| Property | Value |
|----------|-------|
| Format | Unsigned bytes (`"B"`) |
| Dimensions | 1D flat array |
| Size | `width × height × 4` bytes |
| Layout | Row-major, 4 bytes per pixel (RGBA) |
| Writable | Yes |

## Performance Comparison

| Method | Copy? | Use Case |
|--------|-------|----------|
| `memoryview(canvas)` | ❌ No copy | Direct pixel manipulation |
| `np.frombuffer(canvas, ...)` | ❌ No copy | Array operations |
| `texture.blit_buffer(canvas, ...)` | ❌ No copy | Kivy display |
| `bytes(canvas)` | ✅ Copies | Saving, sending over network |
| `canvas.buffer.ptr` | ❌ Raw pointer | C/Cython interop |

!!! warning "Buffer Lifetime"
    The buffer is owned by the `SwCanvas` or `PixelBuffer` object. Don't hold a `memoryview` or NumPy array after the canvas is garbage collected or resized — the underlying memory may be freed.
