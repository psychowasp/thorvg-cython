# Game Development with thorvg-cython

This guide shows how to build real-time games using thorvg-cython for GPU-accelerated vector rendering and [pymunk](http://www.pymunk.org/) for 2D physics.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Kivy App                                       │
│  ┌───────────────────┐  ┌────────────────────┐  │
│  │  Input Handling   │  │  Clock.schedule    │  │
│  └────────┬──────────┘  └────────┬───────────┘  │
│           │                      │               │
│           ▼                      ▼               │
│  ┌────────────────────────────────────────────┐  │
│  │            Game Logic                      │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────┐  │  │
│  │  │ Physics  │  │  Entities │  │  State │  │  │
│  │  │ (pymunk) │  │           │  │        │  │  │
│  │  └──────────┘  └───────────┘  └────────┘  │  │
│  └────────────────────────┬───────────────────┘  │
│                           │                      │
│                           ▼                      │
│  ┌────────────────────────────────────────────┐  │
│  │         thorvg-cython (GlCanvas)           │  │
│  │  Scene Graph → GPU Render → Framebuffer    │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Dependencies

```bash
pip install thorvg-cython kivy pymunk
```

## Project Structure

```
my-game/
├── src/
│   └── my_game/
│       ├── __init__.py
│       ├── game.py         # Main game class
│       ├── physics.py      # Pymunk space setup
│       ├── ship.py         # Player entity
│       ├── constants.py    # Game constants
│       └── hud.py          # Score/lives display
└── pyproject.toml
```

## Physics Setup (pymunk)

```python
import pymunk

# Collision types
CT_SHIP = 1
CT_ASTEROID = 2
CT_BULLET = 3


class Physics:
    """Pymunk physics world."""

    def __init__(self, on_bullet_hit, on_ship_hit):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # Top-down, no gravity

        # Collision handlers
        h1 = self.space.add_collision_handler(CT_BULLET, CT_ASTEROID)
        h1.begin = on_bullet_hit

        h2 = self.space.add_collision_handler(CT_SHIP, CT_ASTEROID)
        h2.begin = on_ship_hit

    def step(self, dt: float):
        self.space.step(dt)

    def add(self, body, shape):
        self.space.add(body, shape)

    def remove(self, shape, body):
        self.space.remove(shape, body)
```

## Game Entity Pattern

Each game entity owns both a **physics body** (pymunk) and **visual shapes** (thorvg):

```python
import math
import pymunk
import thorvg_cython as tvg


class Ship:
    """Player ship with physics and neon vector visuals."""

    def __init__(self, scene: tvg.Scene, physics: Physics, w: float, h: float):
        self._scene = scene
        self._physics = physics
        self._size = 20.0
        self._angle = -math.pi / 2

        # Physics body
        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._body.position = (w / 2, h / 2)
        self._pm_shape = pymunk.Circle(self._body, self._size * 0.7)
        self._pm_shape.collision_type = CT_SHIP
        physics.add(self._body, self._pm_shape)

        # Visual layers (neon bloom effect)
        self._shp_bloom = tvg.Shape()
        self._build_path(self._shp_bloom)
        self._shp_bloom.set_stroke_width(12.0)
        self._shp_bloom.set_stroke_color(0, 255, 200, 38)
        scene.add(self._shp_bloom)

        self._shp_core = tvg.Shape()
        self._build_path(self._shp_core)
        self._shp_core.set_stroke_width(2.0)
        self._shp_core.set_stroke_color(0, 255, 200, 255)
        scene.add(self._shp_core)

    def _build_path(self, shp: tvg.Shape):
        s = self._size
        shp.move_to(s, 0)
        shp.line_to(-s * 0.7, -s * 0.6)
        shp.line_to(-s * 0.4, 0)
        shp.line_to(-s * 0.7, s * 0.6)
        shp.close()

    def sync(self, dt: float):
        """Sync visuals to physics body position."""
        x, y = self._body.position

        # Build transform matrix
        m = tvg.Matrix()
        m.e11 = math.cos(self._angle)
        m.e12 = -math.sin(self._angle)
        m.e21 = math.sin(self._angle)
        m.e22 = math.cos(self._angle)
        m.e13 = x
        m.e23 = y

        self._shp_bloom.set_transform(m)
        self._shp_core.set_transform(m)

    def thrust(self, dt):
        dx = math.cos(self._angle) * 500 * dt
        dy = math.sin(self._angle) * 500 * dt
        vx, vy = self._body.velocity
        self._body.velocity = (vx + dx, vy + dy)

    def rotate(self, direction, dt):
        self._angle += direction * 5.0 * dt
```

## Main Game Class

```python
import thorvg_cython as tvg


class Game:
    """Main game orchestrator using GlCanvas."""

    def __init__(self, canvas: tvg.GlCanvas, w: float, h: float):
        self.canvas = canvas
        self.w, self.h = w, h

        # Scene graph
        self._root = tvg.Scene()
        canvas.add(self._root)

        # Background
        self._bg = tvg.Shape()
        self._bg.append_rect(0, 0, w, h)
        self._bg.set_fill_color(5, 5, 15)
        self._root.add(self._bg)

        # Game layer
        self._game_scene = tvg.Scene()
        self._root.add(self._game_scene)

        # Physics
        self._physics = Physics(self._on_bullet_hit, self._on_ship_hit)

        # Entities
        self._ship = Ship(self._game_scene, self._physics, w, h)

    def tick(self, dt: float):
        """Called every frame from Kivy Clock."""
        dt = min(dt, 0.05)  # Cap dt to avoid spiral of death

        self._physics.step(dt)
        self._ship.sync(dt)

        # Render
        self.canvas.update()
        self.canvas.draw()
        self.canvas.sync()

    def _on_bullet_hit(self, arbiter, space, data):
        # Handle collision...
        pass

    def _on_ship_hit(self, arbiter, space, data):
        # Handle collision...
        pass
```

## Kivy Integration

```python
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Fbo, Rectangle, Color
import thorvg_cython as tvg

tvg.Engine(threads=4)


class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gl_canvas = tvg.GlCanvas()
        self._game = None

        with self.canvas:
            self._fbo = Fbo(size=self.size)
            Color(1, 1, 1, 1)
            self._rect = Rectangle(
                texture=self._fbo.texture,
                size=self.size, pos=self.pos)

        self.bind(size=self._on_resize)
        Clock.schedule_interval(self._tick, 0)

        # Keyboard
        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self._keys_pressed = set()

    def _on_resize(self, *args):
        w, h = int(self.width), int(self.height)
        self._fbo.size = (w, h)
        self._rect.size = self.size
        self._rect.pos = self.pos
        self._rect.texture = self._fbo.texture

        self._fbo.bind()
        self._gl_canvas.target(0, 0, 0, self._fbo.fbo_id, w, h)
        self._game = Game(self._gl_canvas, w, h)
        self._fbo.release()

    def _tick(self, dt):
        if not self._game:
            return

        # Process held keys
        if 'left' in self._keys_pressed:
            self._game._ship.rotate(-1, dt)
        if 'right' in self._keys_pressed:
            self._game._ship.rotate(1, dt)
        if 'up' in self._keys_pressed:
            self._game._ship.thrust(dt)

        self._fbo.bind()
        self._game.tick(dt)
        self._fbo.release()
        self._rect.texture = self._fbo.texture

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        self._keys_pressed.add(keycode[1])


class GameApp(App):
    def build(self):
        return GameWidget()


if __name__ == "__main__":
    GameApp().run()
```

## Real-World Examples

The [kivy-thor-games](https://github.com/Py-Swift/kivy-thor-games/tree/master/games) repository contains complete games built with this architecture:

| Game | Description | Techniques |
|------|-------------|------------|
| **Thor Asteroids** | Classic Asteroids clone | Neon vectors, wraparound physics, particle-like stars |
| **Thor Ball Breaker** | Breakout-style game | Brick collision, paddle physics, score system |
| **Thor Flappy** | Flappy Bird clone | Scrolling world, gap generation |
| **Thor Tempest Run** | Endless runner | Procedural generation, obstacle avoidance |
| **Thor Tetris** | Tetris implementation | Grid logic, piece rotation |

All games use:

- `GlCanvas` for 60fps GPU rendering
- `pymunk` for physics simulation
- Neon vector art style with bloom layers
- Scene graph for entity management
- Matrix transforms for position/rotation sync

## Tips for Game Development

!!! tip "Shape Reuse"
    Instead of creating new shapes each frame, use `shape.reset()` to clear and rebuild geometry, or better yet, use `set_transform()` to move shapes without modifying their path data.

!!! tip "Frame Rate Independence"
    Always multiply velocities and accelerations by `dt` (delta time). Cap `dt` to prevent physics explosions after lag spikes:
    ```python
    dt = min(dt, 0.05)  # Max 50ms per frame
    ```

!!! tip "Collision Types"
    Define collision type constants and register handlers before the game loop starts. Pymunk fires callbacks synchronously during `space.step()`.

!!! tip "Screen Wrapping"
    For games with wrapping (like Asteroids), apply modulo to physics body positions:
    ```python
    x, y = body.position
    body.position = (x % screen_w, y % screen_h)
    ```
