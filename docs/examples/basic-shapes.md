# Basic Shapes

Fundamental shape drawing with thorvg-cython.

## Rectangles

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    # Solid rectangle
    rect = tvg.Shape()
    rect.append_rect(20, 20, 200, 120)
    rect.set_fill_color(66, 135, 245)
    canvas.add(rect)

    # Rounded rectangle
    rounded = tvg.Shape()
    rounded.append_rect(250, 20, 200, 120, rx=25, ry=25)
    rounded.set_fill_color(245, 124, 66)
    canvas.add(rounded)

    # Stroked rectangle
    stroked = tvg.Shape()
    stroked.append_rect(20, 170, 200, 120)
    stroked.set_stroke_width(4.0)
    stroked.set_stroke_color(100, 255, 100)
    canvas.add(stroked)

    canvas.draw()
    canvas.sync()
```

## Circles and Ellipses

```python
with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    # Solid circle
    circle = tvg.Shape()
    circle.append_circle(150, 150, 80, 80)
    circle.set_fill_color(200, 50, 200)
    canvas.add(circle)

    # Ellipse
    ellipse = tvg.Shape()
    ellipse.append_circle(400, 150, 120, 60)
    ellipse.set_fill_color(50, 200, 200)
    canvas.add(ellipse)

    # Stroked circle with dash
    dashed = tvg.Shape()
    dashed.append_circle(300, 300, 70, 70)
    dashed.set_stroke_width(3.0)
    dashed.set_stroke_color(255, 200, 50)
    dashed.set_stroke_dash([15.0, 8.0])
    canvas.add(dashed)

    canvas.draw()
    canvas.sync()
```

## Custom Paths

```python
with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    # Triangle
    tri = tvg.Shape()
    tri.move_to(300, 50)
    tri.line_to(400, 200)
    tri.line_to(200, 200)
    tri.close()
    tri.set_fill_color(255, 100, 100)
    canvas.add(tri)

    # Star
    import math
    star = tvg.Shape()
    cx, cy, outer, inner = 300, 300, 80, 35
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = outer if i % 2 == 0 else inner
        x = cx + math.cos(angle) * r
        y = cy - math.sin(angle) * r
        if i == 0:
            star.move_to(x, y)
        else:
            star.line_to(x, y)
    star.close()
    star.set_fill_color(255, 215, 0)
    canvas.add(star)

    canvas.draw()
    canvas.sync()
```

## Bézier Curves

```python
with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    curve = tvg.Shape()
    curve.move_to(50, 300)
    curve.cubic_to(150, 50, 350, 350, 550, 200)
    curve.set_stroke_width(4.0)
    curve.set_stroke_color(255, 100, 200)
    curve.set_stroke_cap(tvg.StrokeCap.ROUND)
    canvas.add(curve)

    # Multiple curves forming a wave
    wave = tvg.Shape()
    wave.move_to(50, 200)
    for i in range(5):
        x1 = 50 + i * 100 + 25
        x2 = 50 + i * 100 + 75
        x3 = 50 + (i + 1) * 100
        wave.cubic_to(x1, 150, x2, 250, x3, 200)
    wave.set_stroke_width(3.0)
    wave.set_stroke_color(100, 200, 255)
    canvas.add(wave)

    canvas.draw()
    canvas.sync()
```

## Gradients

```python
with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    # Linear gradient
    rect = tvg.Shape()
    rect.append_rect(20, 20, 260, 160, rx=10, ry=10)
    grad = tvg.LinearGradient(20, 20, 280, 180)
    grad.set_color_stops([
        tvg.ColorStop(0.0, 255, 0, 128),
        tvg.ColorStop(1.0, 128, 0, 255),
    ])
    rect.set_gradient(grad)
    canvas.add(rect)

    # Radial gradient
    circle = tvg.Shape()
    circle.append_circle(450, 100, 90, 90)
    rgrad = tvg.RadialGradient(450, 100, 90)
    rgrad.set_color_stops([
        tvg.ColorStop(0.0, 255, 255, 200),
        tvg.ColorStop(0.7, 255, 150, 0),
        tvg.ColorStop(1.0, 150, 50, 0),
    ])
    circle.set_gradient(rgrad)
    canvas.add(circle)

    canvas.draw()
    canvas.sync()
```

## Compositing and Opacity

```python
with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 400)

    # Background
    bg = tvg.Shape()
    bg.append_rect(0, 0, 600, 400)
    bg.set_fill_color(20, 20, 40)
    canvas.add(bg)

    # Overlapping circles with opacity
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    positions = [(200, 180), (300, 180), (250, 260)]

    for (r, g, b), (cx, cy) in zip(colors, positions):
        c = tvg.Shape()
        c.append_circle(cx, cy, 100, 100)
        c.set_fill_color(r, g, b)
        c.set_opacity(160)
        canvas.add(c)

    canvas.draw()
    canvas.sync()
```
