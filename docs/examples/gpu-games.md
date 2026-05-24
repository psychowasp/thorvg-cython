# GPU Games

Complete examples of games built with thorvg-cython's `GlCanvas` for GPU rendering and `pymunk` for physics.

## Asteroids Clone

A full Asteroids game using neon vector graphics, GPU rendering, and physics.

!!! info "Source Code"
    See the complete implementation at [kivy-thor-games/thor-asteroids](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-asteroids).

### Architecture

```python
import math
import random
import pymunk
import thorvg_cython as tvg
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Fbo, Rectangle, Color

tvg.Engine(threads=4)

# Collision types
CT_SHIP = 1
CT_ASTEROID = 2
CT_BULLET = 3


class Physics:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

    def step(self, dt):
        self.space.step(dt)

    def add(self, body, shape):
        self.space.add(body, shape)

    def remove(self, shape, body):
        self.space.remove(shape, body)
```

### Player Ship with Neon Glow

```python
class Ship:
    """Neon vector ship with bloom effect layers."""

    def __init__(self, scene: tvg.Scene, physics: Physics,
                 w: float, h: float):
        self.alive = True
        self._angle = -math.pi / 2
        self._size = 20.0
        self._w, self._h = w, h

        # Physics body
        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._body.position = (w / 2, h / 2)
        self._pm_shape = pymunk.Circle(self._body, self._size * 0.7)
        self._pm_shape.collision_type = CT_SHIP
        physics.add(self._body, self._pm_shape)

        # Visual: 4 layers for neon bloom effect
        self._layers = []
        styles = [
            (12.0, (0, 255, 200, 38)),   # Outer bloom
            (5.0,  (0, 255, 200, 178)),  # Glow
            (2.0,  (0, 255, 200, 255)),  # Core
        ]
        for width, color in styles:
            shp = tvg.Shape()
            self._build_ship_path(shp)
            shp.set_stroke_width(width)
            shp.set_stroke_color(*color)
            shp.set_stroke_join(tvg.StrokeJoin.ROUND)
            scene.add(shp)
            self._layers.append(shp)

        # Fill layer
        fill = tvg.Shape()
        self._build_ship_path(fill)
        fill.set_fill_color(0, 255, 200, 50)
        scene.add(fill)
        self._layers.append(fill)

    def _build_ship_path(self, shp):
        s = self._size
        shp.move_to(s, 0)
        shp.line_to(-s * 0.7, -s * 0.6)
        shp.line_to(-s * 0.4, 0)
        shp.line_to(-s * 0.7, s * 0.6)
        shp.close()

    def thrust(self, dt):
        acc = 500
        dx = math.cos(self._angle) * acc * dt
        dy = math.sin(self._angle) * acc * dt
        vx, vy = self._body.velocity
        self._body.velocity = (vx + dx, vy + dy)

    def rotate(self, direction, dt):
        self._angle += direction * 5.0 * dt

    def sync(self, dt):
        """Update visual transforms from physics."""
        # Drag
        vx, vy = self._body.velocity
        self._body.velocity = (vx * 0.995, vy * 0.995)

        # Screen wrapping
        x, y = self._body.position
        x = x % self._w
        y = y % self._h
        self._body.position = (x, y)

        # Build rotation + translation matrix
        m = tvg.Matrix()
        m.e11 = math.cos(self._angle)
        m.e12 = -math.sin(self._angle)
        m.e21 = math.sin(self._angle)
        m.e22 = math.cos(self._angle)
        m.e13 = x
        m.e23 = y

        for layer in self._layers:
            layer.set_transform(m)
```

### Asteroids with Random Polygons

```python
class Asteroid:
    """Irregular polygon asteroid with physics."""

    def __init__(self, scene: tvg.Scene, physics: Physics,
                 x: float, y: float, size: float):
        self._size = size
        self._angle = 0.0
        self._spin = random.uniform(-2, 2)

        # Physics
        self._body = pymunk.Body(mass=size/10, moment=float('inf'))
        self._body.position = (x, y)
        speed = random.uniform(50, 150)
        angle = random.uniform(0, math.tau)
        self._body.velocity = (
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )
        self._pm_shape = pymunk.Circle(self._body, size * 0.8)
        self._pm_shape.collision_type = CT_ASTEROID
        physics.add(self._body, self._pm_shape)

        # Visual: irregular polygon
        self._layers = []
        for width, alpha in [(8.0, 30), (3.0, 150), (1.5, 255)]:
            shp = tvg.Shape()
            self._build_polygon(shp, size)
            shp.set_stroke_width(width)
            shp.set_stroke_color(200, 200, 200, alpha)
            shp.set_stroke_join(tvg.StrokeJoin.ROUND)
            scene.add(shp)
            self._layers.append(shp)

    def _build_polygon(self, shp, size):
        """Generate irregular asteroid shape."""
        verts = random.randint(8, 12)
        for i in range(verts):
            angle = (i / verts) * math.tau
            r = size * random.uniform(0.7, 1.0)
            x = math.cos(angle) * r
            y = math.sin(angle) * r
            if i == 0:
                shp.move_to(x, y)
            else:
                shp.line_to(x, y)
        shp.close()

    def sync(self, dt, w, h):
        self._angle += self._spin * dt
        x, y = self._body.position
        x = x % w
        y = y % h
        self._body.position = (x, y)

        m = tvg.Matrix()
        m.e11 = math.cos(self._angle)
        m.e12 = -math.sin(self._angle)
        m.e21 = math.sin(self._angle)
        m.e22 = math.cos(self._angle)
        m.e13 = x
        m.e23 = y

        for layer in self._layers:
            layer.set_transform(m)
```

### Game Loop with Kivy

```python
class AsteroidsWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gl_canvas = tvg.GlCanvas()
        self._physics = Physics()
        self._keys = set()

        with self.canvas:
            self._fbo = Fbo(size=(1280, 720))
            Color(1, 1, 1, 1)
            self._rect = Rectangle(
                texture=self._fbo.texture,
                size=self.size, pos=self.pos)

        self._fbo.bind()
        w, h = 1280, 720
        self._gl_canvas.target(0, 0, 0, self._fbo.fbo_id, w, h)

        # Scene
        self._root = tvg.Scene()
        self._gl_canvas.add(self._root)

        bg = tvg.Shape()
        bg.append_rect(0, 0, w, h)
        bg.set_fill_color(5, 5, 15)
        self._root.add(bg)

        game_scene = tvg.Scene()
        self._root.add(game_scene)

        # Entities
        self._ship = Ship(game_scene, self._physics, w, h)
        self._asteroids = []
        for _ in range(5):
            ax = random.uniform(0, w)
            ay = random.uniform(0, h)
            self._asteroids.append(
                Asteroid(game_scene, self._physics, ax, ay, 40))

        self._fbo.release()

        # Input
        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._key_down)
        self._keyboard.bind(on_key_up=self._key_up)

        Clock.schedule_interval(self._tick, 0)

    def _key_down(self, kb, keycode, text, mods):
        self._keys.add(keycode[1])

    def _key_up(self, kb, keycode):
        self._keys.discard(keycode[1])

    def _tick(self, dt):
        dt = min(dt, 0.05)

        if 'left' in self._keys:
            self._ship.rotate(-1, dt)
        if 'right' in self._keys:
            self._ship.rotate(1, dt)
        if 'up' in self._keys:
            self._ship.thrust(dt)

        self._physics.step(dt)
        self._ship.sync(dt)
        for asteroid in self._asteroids:
            asteroid.sync(dt, 1280, 720)

        self._fbo.bind()
        self._gl_canvas.update()
        self._gl_canvas.draw()
        self._gl_canvas.sync()
        self._fbo.release()
        self._rect.texture = self._fbo.texture


class AsteroidsApp(App):
    def build(self):
        return AsteroidsWidget()


if __name__ == "__main__":
    AsteroidsApp().run()
```

## Ball Breaker (Breakout Clone)

A Breakout-style game with brick destruction physics.

!!! info "Source Code"
    See the complete implementation at [kivy-thor-games/thor-ballbreaker](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-ballbreaker).

### Key Patterns

```python
class Brick:
    """Breakable brick with gradient fill."""

    def __init__(self, scene: tvg.Scene, physics: Physics,
                 x: float, y: float, w: float, h: float, color):
        r, g, b = color

        # Physics (static body)
        self._body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self._body.position = (x + w/2, y + h/2)
        self._pm_shape = pymunk.Poly.create_box(self._body, (w, h))
        self._pm_shape.collision_type = CT_BRICK
        physics.add(self._body, self._pm_shape)

        # Visual
        self._shape = tvg.Shape()
        self._shape.append_rect(x, y, w, h, rx=3, ry=3)

        grad = tvg.LinearGradient(x, y, x, y + h)
        grad.set_color_stops([
            tvg.ColorStop(0.0, min(r+60, 255), min(g+60, 255), min(b+60, 255)),
            tvg.ColorStop(1.0, r, g, b),
        ])
        self._shape.set_gradient(grad)
        scene.add(self._shape)

    def destroy(self, scene, physics):
        scene.remove(self._shape)
        physics.remove(self._pm_shape, self._body)
```

## More Games

Check out the complete game collection:

- **[Thor Flappy](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-flappy)** — Flappy Bird with scrolling pipes
- **[Thor Tempest Run](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-tempest-run)** — Endless runner
- **[Thor Tetris](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-tetris)** — Classic Tetris

All games share the same architecture:

1. `GlCanvas` for GPU rendering
2. `pymunk` for physics
3. Scene graph with layered neon vector visuals
4. `Matrix` transforms to sync physics ↔ visuals
5. Kivy `Fbo` for GL context management
