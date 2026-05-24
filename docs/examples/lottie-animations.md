# Lottie Animations

Examples of loading and playing Lottie animations.

## Basic Playback (Headless)

```python
import thorvg_cython as tvg

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(512, 512)

    anim = tvg.LottieAnimation()
    pic = anim.get_picture()
    pic.load("animation.json")
    pic.set_size(512, 512)
    canvas.add(pic)

    # Get animation info
    _, total_frames = anim.get_total_frame()
    _, duration = anim.get_duration()
    print(f"Frames: {total_frames}, Duration: {duration:.2f}s")

    # Render a specific frame
    anim.set_frame(total_frames / 2)  # Middle frame
    canvas.update()
    canvas.draw(True)
    canvas.sync()

    # Save frame
    from PIL import Image
    img = Image.frombytes("RGBA", (512, 512), bytes(canvas))
    img.save("frame_middle.png")
```

## Kivy Lottie Widget

```python
from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import thorvg_cython as tvg

tvg.Engine(threads=4)


class LottieWidget(Image):
    """Animated Lottie widget with play/pause control."""

    def __init__(self, path, width=512, height=512, fps=60,
                 loop=True, **kwargs):
        super().__init__(**kwargs)
        self._w, self._h = width, height
        self._loop = loop
        self._playing = True

        # ThorVG setup
        self._canvas_tvg = tvg.SwCanvas(width, height)
        self._anim = tvg.LottieAnimation()
        pic = self._anim.get_picture()
        pic.load(path)
        pic.set_size(width, height)
        self._canvas_tvg.add(pic)

        # Metadata
        _, self._total_frames = self._anim.get_total_frame()
        _, self._duration = self._anim.get_duration()
        self._frame = 0.0

        # Texture
        self._tex = Texture.create(size=(width, height), colorfmt="rgba")
        self._tex.flip_vertical()
        self._render()

        # Playback
        self._clock_event = Clock.schedule_interval(self._tick, 1.0 / fps)

    def _render(self):
        self._canvas_tvg.update()
        self._canvas_tvg.draw(True)
        self._canvas_tvg.sync()
        self._tex.blit_buffer(
            self._canvas_tvg, colorfmt="rgba", bufferfmt="ubyte")
        self.texture = self._tex

    def _tick(self, dt):
        if not self._playing:
            return

        self._frame += (dt / self._duration) * self._total_frames
        if self._frame >= self._total_frames:
            if self._loop:
                self._frame = 0.0
            else:
                self._frame = self._total_frames - 1
                self._playing = False
                return

        self._anim.set_frame(self._frame)
        self._render()

    def play(self):
        self._playing = True

    def pause(self):
        self._playing = False

    def seek(self, progress: float):
        """Seek to position (0.0 - 1.0)."""
        self._frame = progress * self._total_frames
        self._anim.set_frame(self._frame)
        self._render()

    def set_speed(self, speed: float):
        """Adjust playback speed (1.0 = normal)."""
        self._duration = self._duration / speed


class LottieApp(App):
    def build(self):
        return LottieWidget("loading.json", loop=True)


if __name__ == "__main__":
    LottieApp().run()
```

## Segment Playback

Play only a portion of the animation:

```python
anim = tvg.LottieAnimation()
pic = anim.get_picture()
pic.load("complex_animation.json")
pic.set_size(400, 400)

# Only play frames 30 to 90
anim.set_segment(30, 90)

# Now total_frame reports the segment length
_, segment_frames = anim.get_total_frame()
```

## Marker-Based Playback

If your Lottie file has named markers:

```python
anim = tvg.LottieAnimation()
pic = anim.get_picture()
pic.load("ui_animation.json")
pic.set_size(200, 200)

# List available markers
_, count = anim.get_markers_cnt()
for i in range(count):
    _, name = anim.get_marker(i)
    print(f"Marker {i}: {name}")

# Play a specific marker segment
anim.set_marker("hover_in")
```

## Tweening Between Frames

Smoothly interpolate between two keyframes:

```python
anim = tvg.LottieAnimation()
pic = anim.get_picture()
pic.load("transition.json")
pic.set_size(400, 400)
canvas.add(pic)

# Tween from frame 0 to frame 60 at 50% progress
anim.tween(0, 60, 0.5)  # Shows interpolated frame 30

canvas.update()
canvas.draw(True)
canvas.sync()
```

## Multiple Animations

```python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

class MultiLottieApp(App):
    def build(self):
        layout = BoxLayout(orientation='horizontal', spacing=10)
        animations = ["walk.json", "run.json", "jump.json"]
        for anim_file in animations:
            widget = LottieWidget(anim_file, width=256, height=256, fps=30)
            layout.add_widget(widget)
        return layout
```

## Export Animation Frames

Export every frame as a PNG for video compositing:

```python
import thorvg_cython as tvg
from PIL import Image

with tvg.Engine(threads=4):
    canvas = tvg.SwCanvas(1920, 1080)

    anim = tvg.LottieAnimation()
    pic = anim.get_picture()
    pic.load("intro.json")
    pic.set_size(1920, 1080)
    canvas.add(pic)

    _, total = anim.get_total_frame()
    _, duration = anim.get_duration()
    fps = total / duration

    print(f"Exporting {int(total)} frames at {fps:.1f} fps...")

    for frame in range(int(total)):
        anim.set_frame(float(frame))
        canvas.update()
        canvas.draw(True)
        canvas.sync()

        img = Image.frombytes("RGBA", (1920, 1080), bytes(canvas))
        img.save(f"frames/frame_{frame:05d}.png")

    print("Done! Combine with ffmpeg:")
    print("  ffmpeg -r 60 -i frames/frame_%05d.png -c:v libx264 output.mp4")
```

## Dynamic Slot Override

Modify Lottie properties at runtime:

```python
anim = tvg.LottieAnimation()
pic = anim.get_picture()
pic.load("button.json")
pic.set_size(200, 60)
canvas.add(pic)

# Override a color slot with a JSON patch
slot_json = '{"color": [1, 0, 0, 1]}'  # Red
slot_id = anim.gen_slot(slot_json)
anim.apply_slot(slot_id)

canvas.update()
canvas.draw(True)
canvas.sync()

# Clean up
anim.del_slot(slot_id)
```
