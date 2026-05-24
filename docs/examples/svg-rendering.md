# SVG Rendering

Examples of loading and rendering SVG content with thorvg-cython.

## Load SVG from File

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(800, 600)

    pic = tvg.Picture()
    pic.load("artwork.svg")
    pic.set_size(800, 600)
    canvas.add(pic)

    canvas.draw()
    canvas.sync()

    # Save result
    from PIL import Image
    img = Image.frombytes("RGBA", (800, 600), bytes(canvas))
    img.save("rendered.png")
```

## Load SVG from String

```python
import thorvg_cython as tvg

svg_data = b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF6B6B"/>
      <stop offset="100%" style="stop-color:#4ECDC4"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="20" fill="url(#grad)"/>
  <circle cx="100" cy="100" r="60" fill="white" opacity="0.3"/>
  <text x="100" y="108" text-anchor="middle"
        font-size="24" fill="white" font-family="sans-serif">
    ThorVG
  </text>
</svg>"""

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(400, 400)

    pic = tvg.Picture()
    pic.load_data(svg_data, mimetype="image/svg+xml")
    pic.set_size(400, 400)
    canvas.add(pic)

    canvas.draw()
    canvas.sync()
```

## Multiple SVGs on One Canvas

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(800, 600)

    # Background
    bg = tvg.Shape()
    bg.append_rect(0, 0, 800, 600)
    bg.set_fill_color(30, 30, 50)
    canvas.add(bg)

    # Load multiple SVGs at different positions
    icons = ["home.svg", "settings.svg", "user.svg", "mail.svg"]
    for i, path in enumerate(icons):
        pic = tvg.Picture()
        pic.load(path)
        pic.set_size(100, 100)
        pic.translate(50 + i * 180, 250)
        canvas.add(pic)

    canvas.draw()
    canvas.sync()
```

## SVG with Transforms

```python
import thorvg_cython as tvg
import math

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(600, 600)

    # Center icon and rotate it
    pic = tvg.Picture()
    pic.load("star.svg")
    pic.set_size(200, 200)

    # Position at center with rotation
    m = tvg.Matrix()
    angle = math.radians(45)
    m.e11 = math.cos(angle)
    m.e12 = -math.sin(angle)
    m.e21 = math.sin(angle)
    m.e22 = math.cos(angle)
    m.e13 = 300  # center X
    m.e23 = 300  # center Y
    pic.set_transform(m)

    canvas.add(pic)
    canvas.draw()
    canvas.sync()
```

## SVG Grid Widget (Kivy)

```python
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
import thorvg_cython as tvg

tvg.Engine(threads=4)


class SvgWidget(Image):
    def __init__(self, path, size=128, **kwargs):
        super().__init__(**kwargs)
        canvas_tvg = tvg.SwCanvas(size, size)

        pic = tvg.Picture()
        pic.load(path)
        pic.set_size(size, size)
        canvas_tvg.add(pic)

        canvas_tvg.update()
        canvas_tvg.draw(True)
        canvas_tvg.sync()

        tex = Texture.create(size=(size, size), colorfmt="rgba")
        tex.flip_vertical()
        tex.blit_buffer(canvas_tvg, colorfmt="rgba", bufferfmt="ubyte")
        self.texture = tex


class SvgGridApp(App):
    def build(self):
        grid = GridLayout(cols=4, spacing=10, padding=20)
        for svg in ["icon1.svg", "icon2.svg", "icon3.svg", "icon4.svg",
                    "icon5.svg", "icon6.svg", "icon7.svg", "icon8.svg"]:
            grid.add_widget(SvgWidget(svg, size=96))
        return grid


if __name__ == "__main__":
    SvgGridApp().run()
```

## SVG with Dynamic Overlay

Combine SVG loading with programmatic shapes:

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(400, 400)

    # Load SVG background
    bg_pic = tvg.Picture()
    bg_pic.load("background.svg")
    bg_pic.set_size(400, 400)
    canvas.add(bg_pic)

    # Add programmatic overlay
    badge = tvg.Shape()
    badge.append_circle(350, 50, 25, 25)
    badge.set_fill_color(255, 50, 50)
    canvas.add(badge)

    # Notification count text (if font loaded)
    tvg.Text.font_load("DejaVuSans.ttf")
    text = tvg.Text()
    text.set_font("DejaVuSans")
    text.set_size(18.0)
    text.set_text("3")
    text.set_color(255, 255, 255)
    text.translate(343, 57)
    canvas.add(text)

    canvas.draw()
    canvas.sync()
```
