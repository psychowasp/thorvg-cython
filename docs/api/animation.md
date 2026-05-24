# Animation

thorvg-cython provides `Animation` and `LottieAnimation` classes for playing back animated content.

## Animation

Base class for animation playback control.

### Constructor

```python
anim = tvg.Animation()
```

### `get_picture()`
```python
def get_picture(self) -> Picture
```
Get the animation's picture. Add this to a canvas to render the current frame.

### `set_frame(no)`
```python
def set_frame(self, no: float) -> Result
```
Seek to a specific frame number.

### `get_frame()`
```python
def get_frame(self) -> tuple[Result, float]
```
Get the current frame number.

### `get_total_frame()`
```python
def get_total_frame(self) -> tuple[Result, float]
```
Get the total number of frames.

### `get_duration()`
```python
def get_duration(self) -> tuple[Result, float]
```
Get the total duration in seconds.

### `set_segment(begin, end)`
```python
def set_segment(self, begin: float, end: float) -> Result
```
Restrict playback to a frame range.

### `get_segment()`
```python
def get_segment(self) -> tuple[Result, float, float]
```

---

## LottieAnimation

Extended animation class with Lottie-specific features like slots, markers, and tweening.

### Constructor

```python
anim = tvg.LottieAnimation()
```

### Slot Manipulation

#### `gen_slot(slot)`
```python
def gen_slot(self, slot: str) -> int
```
Generate a slot override from a JSON string. Returns a slot ID.

#### `apply_slot(id)`
```python
def apply_slot(self, id: int) -> Result
```
Apply a previously generated slot.

#### `del_slot(id)`
```python
def del_slot(self, id: int) -> Result
```
Delete a slot override.

### Markers

#### `set_marker(marker)`
```python
def set_marker(self, marker: str) -> Result
```
Set playback to a named marker segment.

#### `get_markers_cnt()`
```python
def get_markers_cnt(self) -> tuple[Result, int]
```

#### `get_marker(idx)`
```python
def get_marker(self, idx: int) -> tuple[Result, str | None]
```

### Tweening

#### `tween(from_, to, progress)`
```python
def tween(self, from_: float, to: float, progress: float) -> Result
```
Interpolate between two frames. `progress` is 0.0–1.0.

### Property Assignment

#### `assign(layer, ix, var, val)`
```python
def assign(self, layer: str, ix: int, var: str, val: float) -> Result
```
Assign a value to a Lottie property at runtime.

### Quality

#### `set_quality(value)`
```python
def set_quality(self, value: int) -> Result
```
Set rendering quality (0–100).

---

## Example: Lottie Playback Loop

```python
import thorvg_cython as tvg
from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

tvg.Engine(threads=4)


class LottieWidget(Image):
    def __init__(self, path, width=512, height=512, fps=60, **kwargs):
        super().__init__(**kwargs)
        self._canvas_tvg = tvg.SwCanvas(width, height)

        # Create animation and load the Lottie file
        self._anim = tvg.LottieAnimation()
        pic = self._anim.get_picture()
        pic.load(path)
        pic.set_size(width, height)
        self._canvas_tvg.add(pic)

        # Get animation metadata
        _, self._total_frames = self._anim.get_total_frame()
        _, self._duration = self._anim.get_duration()
        self._current_frame = 0.0

        # Create texture
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
        self._current_frame += (dt / self._duration) * self._total_frames
        if self._current_frame >= self._total_frames:
            self._current_frame = 0.0
        self._anim.set_frame(self._current_frame)
        self._render()


class LottieApp(App):
    def build(self):
        return LottieWidget("animation.json")


if __name__ == "__main__":
    LottieApp().run()
```

## Example: Headless Animation Export

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(800, 600)

    anim = tvg.LottieAnimation()
    pic = anim.get_picture()
    pic.load("animation.json")
    pic.set_size(800, 600)
    canvas.add(pic)

    _, total = anim.get_total_frame()

    # Export every 10th frame
    for frame in range(0, int(total), 10):
        anim.set_frame(float(frame))
        canvas.update()
        canvas.draw(True)
        canvas.sync()

        from PIL import Image
        img = Image.frombytes("RGBA", (800, 600), bytes(canvas))
        img.save(f"frame_{frame:04d}.png")
```
