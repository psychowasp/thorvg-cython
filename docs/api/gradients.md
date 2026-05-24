# Gradients

thorvg-cython supports linear and radial gradients for both fill and stroke.

## LinearGradient

### Constructor

```python
grad = tvg.LinearGradient(x1=0, y1=0, x2=100, y2=0)
```

Creates a linear gradient from point `(x1, y1)` to `(x2, y2)`.

### `set(x1, y1, x2, y2)`
```python
def set(self, x1: float, y1: float, x2: float, y2: float) -> Result
```

### `get()`
```python
def get(self) -> tuple[Result, float, float, float, float]
```

## RadialGradient

### Constructor

```python
grad = tvg.RadialGradient(cx=100, cy=100, radius=50, fx=100, fy=100, fr=0)
```

| Parameter | Description |
|-----------|-------------|
| `cx`, `cy` | Center of the gradient |
| `radius` | Outer radius |
| `fx`, `fy` | Focal point |
| `fr` | Focal radius |

### `set(cx, cy, r, fx=0, fy=0, fr=0)`
```python
def set(self, cx: float, cy: float, r: float,
        fx: float = 0, fy: float = 0, fr: float = 0) -> Result
```

### `get()`
```python
def get(self) -> tuple[Result, float, float, float, float, float, float]
```

## Common Methods (Gradient Base)

### `set_color_stops(stops)`
```python
def set_color_stops(self, stops: Sequence[ColorStop]) -> Result
```
Define gradient color stops. Each `ColorStop` has an offset (0.0–1.0) and RGBA color.

```python
grad.set_color_stops([
    tvg.ColorStop(0.0, 255, 0, 0),      # Red at start
    tvg.ColorStop(0.5, 255, 255, 0),     # Yellow at middle
    tvg.ColorStop(1.0, 0, 255, 0),       # Green at end
])
```

### `get_color_stops()`
```python
def get_color_stops(self) -> tuple[Result, list[ColorStop]]
```

### `set_spread(spread)`
```python
def set_spread(self, spread: int) -> Result
```
Set how the gradient fills beyond its defined range:

- `StrokeFill.PAD` — Extend edge colors (default)
- `StrokeFill.REFLECT` — Mirror the gradient
- `StrokeFill.REPEAT` — Tile the gradient

### `set_transform(m)`
```python
def set_transform(self, m: Matrix) -> Result
```
Apply a transform to the gradient coordinates.

### `duplicate()`
```python
def duplicate(self) -> Gradient | None
```
Deep copy the gradient.

## Examples

### Linear Gradient Fill

```python
import thorvg_cython as tvg

shape = tvg.Shape()
shape.append_rect(0, 0, 300, 200, rx=10, ry=10)

grad = tvg.LinearGradient(0, 0, 300, 200)
grad.set_color_stops([
    tvg.ColorStop(0.0, 128, 0, 255),    # Purple
    tvg.ColorStop(0.5, 255, 0, 128),    # Pink
    tvg.ColorStop(1.0, 255, 128, 0),    # Orange
])
shape.set_gradient(grad)
canvas.add(shape)
```

### Radial Gradient with Focal Point

```python
circle = tvg.Shape()
circle.append_circle(200, 200, 100, 100)

# Off-center focal point for a 3D sphere effect
grad = tvg.RadialGradient(200, 200, 100, fx=170, fy=170, fr=10)
grad.set_color_stops([
    tvg.ColorStop(0.0, 255, 255, 255),  # White highlight
    tvg.ColorStop(0.5, 100, 150, 255),  # Blue
    tvg.ColorStop(1.0, 20, 40, 100),    # Dark blue edge
])
circle.set_gradient(grad)
canvas.add(circle)
```

### Gradient Stroke

```python
path = tvg.Shape()
path.move_to(50, 150)
path.cubic_to(100, 50, 200, 250, 350, 150)
path.set_stroke_width(8.0)
path.set_stroke_cap(tvg.StrokeCap.ROUND)

stroke_grad = tvg.LinearGradient(50, 0, 350, 0)
stroke_grad.set_color_stops([
    tvg.ColorStop(0.0, 255, 0, 100),
    tvg.ColorStop(1.0, 100, 0, 255),
])
path.set_stroke_gradient(stroke_grad)
canvas.add(path)
```

### Repeating Gradient

```python
grad = tvg.LinearGradient(0, 0, 50, 0)  # Short range
grad.set_color_stops([
    tvg.ColorStop(0.0, 255, 255, 0),
    tvg.ColorStop(1.0, 255, 0, 0),
])
grad.set_spread(tvg.StrokeFill.REPEAT)  # Tiles across the shape

shape = tvg.Shape()
shape.append_rect(0, 0, 400, 100)
shape.set_gradient(grad)
canvas.add(shape)
```
