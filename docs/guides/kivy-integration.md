# Kivy Integration

thorvg-cython integrates seamlessly with [Kivy](https://kivy.org) thanks to its PEP 3118 buffer protocol support. This guide covers both software (CPU) and GPU rendering within Kivy applications.

## SVG Widget (Software Rendering)

The simplest integration: render an SVG to a Kivy `Image` widget.

```python
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
import thorvg_cython as tvg

# Initialize once at module level
tvg.Engine(threads=4)


class SvgWidget(Image):
    """Render an SVG file as a Kivy Image."""

    def __init__(self, path, width=512, height=512, **kwargs):
        super().__init__(**kwargs)
        canvas_tvg = tvg.SwCanvas(width, height)

        pic = tvg.Picture()
        pic.load(path)
        pic.set_size(width, height)
        canvas_tvg.add(pic)

        canvas_tvg.update()
        canvas_tvg.draw(True)
        canvas_tvg.sync()

        tex = Texture.create(size=(width, height), colorfmt="rgba")
        tex.flip_vertical()
        # Zero-copy blit — canvas_tvg supports buffer protocol
        tex.blit_buffer(canvas_tvg, colorfmt="rgba", bufferfmt="ubyte")
        self.texture = tex


class MyApp(App):
    def build(self):
        return SvgWidget("logo.svg")


if __name__ == "__main__":
    MyApp().run()
```

## Inline SVG Widget

Render SVG directly from bytes:

```python
class SvgDataWidget(Image):
    """Render SVG from in-memory bytes."""

    def __init__(self, data: bytes, width=400, height=400, **kwargs):
        super().__init__(**kwargs)
        canvas_tvg = tvg.SwCanvas(width, height)

        pic = tvg.Picture()
        pic.load_data(data, mimetype="image/svg+xml")
        pic.set_size(width, height)
        canvas_tvg.add(pic)

        canvas_tvg.update()
        canvas_tvg.draw(True)
        canvas_tvg.sync()

        tex = Texture.create(size=(width, height), colorfmt="rgba")
        tex.flip_vertical()
        tex.blit_buffer(canvas_tvg, colorfmt="rgba", bufferfmt="ubyte")
        self.texture = tex
```

## Lottie Animation Widget

Animate Lottie files at 60fps:

```python
from kivy.clock import Clock


class LottieWidget(Image):
    """Play a Lottie animation in a Kivy widget."""

    def __init__(self, path, width=512, height=512, fps=60, **kwargs):
        super().__init__(**kwargs)
        self._canvas_tvg = tvg.SwCanvas(width, height)

        # Load animation
        self._anim = tvg.LottieAnimation()
        pic = self._anim.get_picture()
        pic.load(path)
        pic.set_size(width, height)
        self._canvas_tvg.add(pic)

        # Animation metadata
        _, self._total_frames = self._anim.get_total_frame()
        _, self._duration = self._anim.get_duration()
        self._frame = 0.0

        # Texture
        self._tex = Texture.create(size=(width, height), colorfmt="rgba")
        self._tex.flip_vertical()
        self._render()

        # Start playback
        Clock.schedule_interval(self._tick, 1.0 / fps)

    def _render(self):
        self._canvas_tvg.update()
        self._canvas_tvg.draw(True)
        self._canvas_tvg.sync()
        self._tex.blit_buffer(
            self._canvas_tvg, colorfmt="rgba", bufferfmt="ubyte")
        self.texture = self._tex

    def _tick(self, dt):
        self._frame += (dt / self._duration) * self._total_frames
        if self._frame >= self._total_frames:
            self._frame = 0.0
        self._anim.set_frame(self._frame)
        self._render()
```

## GPU Rendering in Kivy

For high-performance real-time rendering, use `GlCanvas` with Kivy's OpenGL context:

```python
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Fbo, Color, Rectangle, Callback
from kivy.graphics.opengl import glGetIntegerv, GL_FRAMEBUFFER_BINDING
import thorvg_cython as tvg

tvg.Engine(threads=4)


class GpuVectorWidget(Widget):
    """Widget that renders vector graphics on the GPU via GlCanvas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gl_canvas = tvg.GlCanvas()
        self._initialized = False

        with self.canvas:
            self._fbo = Fbo(size=self.size)
            Color(1, 1, 1, 1)
            self._rect = Rectangle(
                texture=self._fbo.texture,
                size=self.size, pos=self.pos)

        self.bind(size=self._on_resize, pos=self._on_resize)
        Clock.schedule_interval(self._render, 1.0 / 60)

    def _setup_scene(self, w, h):
        """Build the ThorVG scene graph."""
        self._root = tvg.Scene()
        self._gl_canvas.add(self._root)

        # Background
        bg = tvg.Shape()
        bg.append_rect(0, 0, w, h)
        bg.set_fill_color(15, 15, 25)
        self._root.add(bg)

        # Add your shapes here...
        self._circle = tvg.Shape()
        self._circle.append_circle(w/2, h/2, 100, 100)
        self._circle.set_fill_color(0, 200, 255)
        self._root.add(self._circle)

    def _on_resize(self, *args):
        w, h = int(self.width), int(self.height)
        self._fbo.size = (w, h)
        self._rect.size = self.size
        self._rect.pos = self.pos
        self._rect.texture = self._fbo.texture
        self._initialized = False

    def _render(self, dt):
        w, h = int(self.width), int(self.height)
        if w <= 0 or h <= 0:
            return

        self._fbo.bind()

        if not self._initialized:
            fbo_id = self._fbo.fbo_id
            self._gl_canvas.target(0, 0, 0, fbo_id, w, h)
            self._setup_scene(w, h)
            self._initialized = True

        # Update and render
        self._gl_canvas.update()
        self._gl_canvas.draw()
        self._gl_canvas.sync()

        self._fbo.release()
        self._rect.texture = self._fbo.texture


class GpuApp(App):
    def build(self):
        return GpuVectorWidget()


if __name__ == "__main__":
    GpuApp().run()
```

## Multiple SVGs in a Grid

```python
from kivy.app import App
from kivy.uix.gridlayout import GridLayout

class SvgGrid(App):
    def build(self):
        grid = GridLayout(cols=3, spacing=10, padding=10)
        svgs = ["icon1.svg", "icon2.svg", "icon3.svg",
                "icon4.svg", "icon5.svg", "icon6.svg"]
        for svg in svgs:
            grid.add_widget(SvgWidget(svg, 128, 128))
        return grid
```

## Tips

!!! tip "Zero-Copy Performance"
    `SwCanvas` and `PixelBuffer` support the buffer protocol, so `blit_buffer()` never copies data — it reads directly from the ThorVG render buffer.

!!! tip "Engine Initialization"
    Initialize `tvg.Engine()` once at module level, not per-widget. ThorVG is a singleton.

!!! tip "Texture Flip"
    Kivy's texture origin is bottom-left while ThorVG renders top-left. Always call `tex.flip_vertical()` after creating the texture.
