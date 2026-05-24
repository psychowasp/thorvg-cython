# Quick Start

This guide walks you through the fundamentals of thorvg-cython in just a few minutes.

## Core Concepts

thorvg-cython follows a simple pipeline:

1. **Initialize** the engine
2. **Create** a canvas (software or GPU)
3. **Build** paints (shapes, pictures, scenes, text)
4. **Add** paints to the canvas
5. **Draw** and **sync** to produce pixels

## Hello, ThorVG!

```python
import thorvg_cython as tvg

# 1. Initialize the engine (use context manager for auto-cleanup)
with tvg.Engine(threads=2) as engine:
    # 2. Create a software canvas with a 400x300 pixel buffer
    canvas = tvg.SwCanvas(400, 300)

    # 3. Create a shape and define its geometry
    shape = tvg.Shape()
    shape.append_rect(50, 50, 300, 200, rx=15, ry=15)
    shape.set_fill_color(100, 180, 255)  # Light blue

    # 4. Add the shape to the canvas
    canvas.add(shape)

    # 5. Render
    canvas.draw()
    canvas.sync()

    # Access the rendered pixels
    print(f"Buffer size: {len(canvas)} bytes")  # 400*300*4 = 480,000
```

## Drawing Shapes

### Rectangles

```python
shape = tvg.Shape()
shape.append_rect(x=10, y=10, w=200, h=100, rx=0, ry=0)
shape.set_fill_color(255, 100, 50)  # Orange
canvas.add(shape)
```

### Circles and Ellipses

```python
circle = tvg.Shape()
circle.append_circle(cx=200, cy=150, rx=80, ry=80)
circle.set_fill_color(50, 200, 100)  # Green
canvas.add(circle)

# Ellipse (different rx and ry)
ellipse = tvg.Shape()
ellipse.append_circle(cx=200, cy=150, rx=120, ry=60)
ellipse.set_fill_color(200, 50, 200)  # Purple
canvas.add(ellipse)
```

### Custom Paths

```python
path = tvg.Shape()
path.move_to(100, 50)
path.line_to(200, 150)
path.line_to(50, 150)
path.close()
path.set_fill_color(255, 200, 0)  # Yellow triangle
canvas.add(path)
```

### Bézier Curves

```python
curve = tvg.Shape()
curve.move_to(50, 200)
curve.cubic_to(100, 50, 200, 350, 250, 200)
curve.set_stroke_width(3.0)
curve.set_stroke_color(255, 255, 255)
canvas.add(curve)
```

## Strokes

```python
shape = tvg.Shape()
shape.append_rect(20, 20, 160, 120, rx=10, ry=10)

# Fill
shape.set_fill_color(30, 30, 50)

# Stroke styling
shape.set_stroke_width(4.0)
shape.set_stroke_color(0, 255, 200)
shape.set_stroke_cap(tvg.StrokeCap.ROUND)
shape.set_stroke_join(tvg.StrokeJoin.ROUND)

# Dashed stroke
shape.set_stroke_dash([10.0, 5.0, 3.0, 5.0])

canvas.add(shape)
```

## Transforms

Every paint supports translation, rotation, scaling, and full matrix transforms:

```python
shape = tvg.Shape()
shape.append_rect(0, 0, 100, 50)
shape.set_fill_color(255, 0, 0)

# Simple transforms
shape.translate(200, 150)
shape.rotate(45)  # degrees
shape.scale(1.5)

# Or use a full 3x3 matrix
import math
angle = math.radians(30)
m = tvg.Matrix(
    e11=math.cos(angle), e12=-math.sin(angle), e13=100,
    e21=math.sin(angle), e22=math.cos(angle),  e23=100,
)
shape.set_transform(m)

canvas.add(shape)
```

## Loading SVG Files

```python
pic = tvg.Picture()
pic.load("icon.svg")
pic.set_size(200, 200)
canvas.add(pic)
```

## Loading Inline SVG

```python
svg_data = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="#FF6B6B"/>
</svg>"""

pic = tvg.Picture()
pic.load_data(svg_data, mimetype="image/svg+xml")
pic.set_size(200, 200)
canvas.add(pic)
```

## Opacity and Visibility

```python
shape = tvg.Shape()
shape.append_circle(100, 100, 50, 50)
shape.set_fill_color(255, 0, 0)

# Semi-transparent (0=invisible, 255=fully opaque)
shape.set_opacity(128)

# Hide/show
shape.set_visible(False)
shape.set_visible(True)
```

## Scenes (Grouping)

Scenes let you group paints together for collective transforms and effects:

```python
scene = tvg.Scene()

# Add multiple shapes to the scene
rect = tvg.Shape()
rect.append_rect(0, 0, 100, 100)
rect.set_fill_color(255, 0, 0)
scene.add(rect)

circle = tvg.Shape()
circle.append_circle(50, 50, 30, 30)
circle.set_fill_color(0, 0, 255)
scene.add(circle)

# Transform the entire group
scene.translate(100, 100)
scene.rotate(15)

canvas.add(scene)
```

## Complete Example: Rendering to a PNG

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4) as engine:
    canvas = tvg.SwCanvas(800, 600)

    # Background
    bg = tvg.Shape()
    bg.append_rect(0, 0, 800, 600)
    bg.set_fill_color(20, 20, 30)
    canvas.add(bg)

    # Gradient circle
    circle = tvg.Shape()
    circle.append_circle(400, 300, 150, 150)

    grad = tvg.RadialGradient(400, 300, 150)
    grad.set_color_stops([
        tvg.ColorStop(0.0, 255, 100, 50),
        tvg.ColorStop(1.0, 100, 0, 200),
    ])
    circle.set_gradient(grad)
    canvas.add(circle)

    # Render
    canvas.draw()
    canvas.sync()

    # Save as PNG (requires Pillow)
    from PIL import Image
    img = Image.frombytes("RGBA", (800, 600), bytes(canvas))
    img.save("output.png")
```

## Next Steps

- [API Reference](../api/overview.md) — Full class and method documentation
- [GPU Rendering](../guides/gpu-rendering.md) — Hardware-accelerated rendering
- [Kivy Integration](../guides/kivy-integration.md) — Use with the Kivy framework
- [Game Development](../guides/game-development.md) — Build games with physics
