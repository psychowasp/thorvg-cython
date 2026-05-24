# Shape

`Shape` is the primary vector drawing primitive. It supports paths, rectangles, circles, strokes, fills, and gradients.

## Constructor

```python
shape = tvg.Shape()
```

## Path Building

### `move_to(x, y)`
```python
def move_to(self, x: float, y: float) -> Result
```
Move the pen to `(x, y)` without drawing.

### `line_to(x, y)`
```python
def line_to(self, x: float, y: float) -> Result
```
Draw a straight line from the current position to `(x, y)`.

### `cubic_to(cx1, cy1, cx2, cy2, x, y)`
```python
def cubic_to(self, cx1: float, cy1: float, cx2: float, cy2: float,
             x: float, y: float) -> Result
```
Draw a cubic Bézier curve with control points `(cx1,cy1)`, `(cx2,cy2)` and endpoint `(x,y)`.

### `close()`
```python
def close(self) -> Result
```
Close the current sub-path by connecting to the starting point.

### `reset()`
```python
def reset(self) -> Result
```
Clear all path data. Use before rebuilding the shape geometry.

### `append_rect(x, y, w, h, rx=0, ry=0, cw=True)`
```python
def append_rect(self, x: float, y: float, w: float, h: float,
                rx: float = 0, ry: float = 0, cw: bool = True) -> Result
```
Append a rectangle. `rx`/`ry` control corner rounding.

```python
# Sharp corners
shape.append_rect(10, 10, 200, 100)

# Rounded corners
shape.append_rect(10, 10, 200, 100, rx=20, ry=20)
```

### `append_circle(cx, cy, rx, ry, cw=True)`
```python
def append_circle(self, cx: float, cy: float, rx: float, ry: float,
                  cw: bool = True) -> Result
```
Append a circle or ellipse centered at `(cx, cy)`.

```python
# Circle (equal radii)
shape.append_circle(100, 100, 50, 50)

# Ellipse
shape.append_circle(100, 100, 80, 40)
```

### `append_path(commands, points)`
```python
def append_path(self, commands: Sequence[PathCommand],
                points: Sequence[Point | tuple]) -> Result
```
Append a raw path from command/point arrays.

```python
commands = [tvg.PathCommand.MOVE_TO, tvg.PathCommand.LINE_TO,
            tvg.PathCommand.LINE_TO, tvg.PathCommand.CLOSE]
points = [(50, 10), (90, 90), (10, 90)]
shape.append_path(commands, points)
```

### `get_path()`
```python
def get_path(self) -> tuple[Result, list[PathCommand], list[Point]]
```
Get the current path data.

## Fill

### `set_fill_color(r, g, b, a=255)`
```python
def set_fill_color(self, r: int, g: int, b: int, a: int = 255) -> Result
```

### `get_fill_color()`
```python
def get_fill_color(self) -> tuple[Result, int, int, int, int]
```

### `set_fill_rule(rule)`
```python
def set_fill_rule(self, rule: int) -> Result
```
Set the fill rule: `FillRule.NON_ZERO` or `FillRule.EVEN_ODD`.

### `set_gradient(grad)`
```python
def set_gradient(self, grad: Gradient) -> Result
```
Fill with a gradient instead of a solid color.

```python
grad = tvg.LinearGradient(0, 0, 200, 0)
grad.set_color_stops([
    tvg.ColorStop(0.0, 255, 0, 0),
    tvg.ColorStop(1.0, 0, 0, 255),
])
shape.set_gradient(grad)
```

### `set_paint_order(stroke_first)`
```python
def set_paint_order(self, stroke_first: bool) -> Result
```
Control whether stroke or fill renders first.

## Stroke

### `set_stroke_width(width)`
```python
def set_stroke_width(self, width: float) -> Result
```

### `set_stroke_color(r, g, b, a=255)`
```python
def set_stroke_color(self, r: int, g: int, b: int, a: int = 255) -> Result
```

### `set_stroke_gradient(grad)`
```python
def set_stroke_gradient(self, grad: Gradient) -> Result
```

### `set_stroke_dash(pattern, offset=0)`
```python
def set_stroke_dash(self, pattern: Sequence[float], offset: float = 0) -> Result
```
Create a dashed stroke. `pattern` alternates between dash and gap lengths.

```python
# 10px dash, 5px gap, repeating
shape.set_stroke_dash([10.0, 5.0])
```

### `set_stroke_cap(cap)`
```python
def set_stroke_cap(self, cap: int) -> Result
```
Line cap style: `StrokeCap.BUTT`, `StrokeCap.ROUND`, or `StrokeCap.SQUARE`.

### `set_stroke_join(join)`
```python
def set_stroke_join(self, join: int) -> Result
```
Line join style: `StrokeJoin.MITER`, `StrokeJoin.ROUND`, or `StrokeJoin.BEVEL`.

### `set_stroke_miterlimit(ml)`
```python
def set_stroke_miterlimit(self, ml: float) -> Result
```

### `set_trimpath(begin, end, simultaneous=False)`
```python
def set_trimpath(self, begin: float, end: float,
                 simultaneous: bool = False) -> Result
```
Trim the stroke path. `begin` and `end` are in range [0.0, 1.0].

```python
# Show only the first half of the stroke
shape.set_trimpath(0.0, 0.5)
```

## Complete Example

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(400, 400)

    # Neon ring
    ring = tvg.Shape()
    ring.append_circle(200, 200, 150, 150)
    ring.set_stroke_width(6.0)
    ring.set_stroke_color(0, 255, 200)
    ring.set_stroke_cap(tvg.StrokeCap.ROUND)
    ring.set_trimpath(0.0, 0.75)
    canvas.add(ring)

    # Gradient rectangle
    rect = tvg.Shape()
    rect.append_rect(100, 100, 200, 200, rx=15, ry=15)
    grad = tvg.LinearGradient(100, 100, 300, 300)
    grad.set_color_stops([
        tvg.ColorStop(0.0, 255, 50, 50),
        tvg.ColorStop(0.5, 50, 255, 50),
        tvg.ColorStop(1.0, 50, 50, 255),
    ])
    rect.set_gradient(grad)
    canvas.add(rect)

    canvas.draw()
    canvas.sync()
```
