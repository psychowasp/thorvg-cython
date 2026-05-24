# Picture

`Picture` loads and renders external image content: SVG files, Lottie JSON, and raw pixel data.

## Constructor

```python
pic = tvg.Picture()
```

## Loading

### `load(path)`
```python
def load(self, path: str) -> Result
```
Load from a file path. Supported formats: SVG, Lottie JSON, TVG, PNG, JPG, WebP.

```python
pic = tvg.Picture()
pic.load("icon.svg")
```

### `load_data(data, mimetype="", rpath="", copy=True)`
```python
def load_data(self, data: bytes, mimetype: str = "",
              rpath: str = "", copy: bool = True) -> Result
```
Load from in-memory bytes.

| Parameter | Description |
|-----------|-------------|
| `data` | Raw file content as bytes |
| `mimetype` | Content type hint (e.g., `"image/svg+xml"`) |
| `rpath` | Resource path for resolving relative references |
| `copy` | If `True`, copies the data internally |

```python
svg_bytes = b'<svg xmlns="http://www.w3.org/2000/svg">...</svg>'
pic = tvg.Picture()
pic.load_data(svg_bytes, mimetype="image/svg+xml")
```

### `load_raw(data_ptr, w, h, cs=0, copy=True)`
```python
def load_raw(self, data_ptr: int, w: int, h: int,
             cs: int = 0, copy: bool = True) -> Result
```
Load from a raw pixel pointer. For advanced interop scenarios.

## Size and Position

### `set_size(w, h)`
```python
def set_size(self, w: float, h: float) -> Result
```
Set the display size. The content is scaled to fit.

### `get_size()`
```python
def get_size(self) -> tuple[Result, float, float]
```

### `set_origin(x, y)`
```python
def set_origin(self, x: float, y: float) -> Result
```
Set the origin point for transforms.

### `get_origin()`
```python
def get_origin(self) -> tuple[Result, float, float]
```

## Sub-Paint Access

### `get_paint(id)`
```python
def get_paint(self, id: int) -> Paint | None
```
Get a specific sub-paint by its ID (useful for SVG element access).

## Examples

### Render an SVG to a Kivy texture

```python
import thorvg_cython as tvg
from kivy.graphics.texture import Texture

tvg.Engine(threads=4)

canvas = tvg.SwCanvas(512, 512)
pic = tvg.Picture()
pic.load("logo.svg")
pic.set_size(512, 512)
canvas.add(pic)

canvas.update()
canvas.draw(True)
canvas.sync()

tex = Texture.create(size=(512, 512), colorfmt="rgba")
tex.flip_vertical()
tex.blit_buffer(canvas, colorfmt="rgba", bufferfmt="ubyte")
```

### Load inline SVG data

```python
svg = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#4A90D9" rx="10"/>
  <circle cx="50" cy="50" r="30" fill="white"/>
</svg>"""

pic = tvg.Picture()
pic.load_data(svg, mimetype="image/svg+xml")
pic.set_size(200, 200)
canvas.add(pic)
```
