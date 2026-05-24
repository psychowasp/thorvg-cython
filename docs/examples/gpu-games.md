# GPU Games

Two complete games built with thorvg-cython's `GlCanvas` for GPU rendering — one
**without** physics (Flappy Bird) and one **with** pymunk physics (Tetris).

Both games inherit from `thorvg_cython.Scene` directly: the game *is* the root
scene. You add it to a `GlCanvas` and call `tick(dt)` each frame.

---

## Flappy Bird (no pymunk)

A pure thorvg-cython game — no physics library, just velocity + gravity on a
single bird sprite. Demonstrates **scene composition**, **scrolling parallax
layers**, and **AABB collision** against scrolling pipes.

!!! info "Source code"
    [kivy-thor-games/games/thor-flappy](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-flappy)

### Scene as the game

`FlappyScene` inherits `Scene` directly. There's no separate "game world" —
the scene *is* the world.

```python
from thorvg_cython import Scene
from .constants import GRAVITY, GROUND_H, DESIGN_H, IDLE, PLAYING, DEAD, mat
from .sky import Sky
from .clouds import BgCloudLayer, CloudLayer
from .trees import TreeLayer
from .bushes import BushLayer
from .pipes import PipeLayer
from .ground import Ground
from .bird import Bird
from .hud import Hud


class FlappyScene(Scene):
    def __init__(self, font='Roboto-Regular', font_bold='Roboto-Bold'):
        super().__init__()
        self._state = IDLE
        self._score = 0

        # Parallax layers (back-to-front)
        self._sky       = Sky(self, DESIGN_H, DESIGN_H)
        self._bg_clouds = BgCloudLayer(self, DESIGN_H, DESIGN_H)
        self._clouds    = CloudLayer(self, DESIGN_H, DESIGN_H)
        self._trees     = TreeLayer(self, DESIGN_H, DESIGN_H)
        self._bushes    = BushLayer(self, DESIGN_H, DESIGN_H)
        self._pipes     = PipeLayer(self, DESIGN_H)
        self._ground    = Ground(self, DESIGN_H, DESIGN_H)
        self._bird      = Bird(self)

        self._hud = Hud(0, 0, font=font, font_bold=font_bold)
        self._hud.show_message('TAP TO PLAY')
```

### Manual physics — no library

The bird carries its own `vy` (vertical velocity). Each frame, gravity adds to
`vy`, and `vy` adds to `y`. That's it.

```python
class Bird(Scene):
    RADIUS = 20

    def __init__(self, canvas):
        super().__init__()
        self.x  = 0.0
        self.y  = 0.0
        self.vy = 0.0
        self._wing  = Shape(); self.add(self._wing)
        self._body  = Shape(); self.add(self._body)
        self._beak  = Shape(); self.add(self._beak)
        canvas.add(self)

    def jump(self):
        self.vy = JUMP_VEL          # negative — instant upward kick

    def apply_gravity(self, dt):
        self.vy += GRAVITY * dt
        self.y  += self.vy * dt

    def hits_ceiling_or_ground(self, ground_y, r=15):
        return self.y - r <= 0 or self.y + r >= ground_y
```

### Drawing — gradients for the body

The bird body uses a `RadialGradient` for the highlight, drawn into a `Shape`
each frame with a rotation matrix derived from `vy`.

```python
def draw(self, angle_deg=None):
    if angle_deg is None:
        angle_deg = max(-28.0, min(90.0, self.vy * 0.05))
    m = rot(math.radians(angle_deg), self.x, self.y)

    self._body.reset()
    self._body.append_circle(0, 0, self.RADIUS, self.RADIUS)
    rg = RadialGradient()
    rg.set(-6, -6, self.RADIUS)
    rg.set_color_stops([
        ColorStop(0.0,  255, 242,  80, 255),
        ColorStop(0.55, 252, 192,  22, 255),
        ColorStop(1.0,  215, 135,   0, 255),
    ])
    self._body.set_gradient(rg)
    self._body.set_transform(m)
```

### Per-frame tick

```python
def tick(self, dt: float):
    dt = min(dt, 0.05)
    ground_y = DESIGN_H - GROUND_H

    if self._state == PLAYING:
        self._bg_clouds.update(dt, self._logical_w)
        self._clouds.update(dt, self._logical_w)
        self._trees.update(dt, self._logical_w)
        self._bushes.update(dt, self._logical_w)

        self._bird.apply_gravity(dt)
        self._bird.draw()
        self._pipes.tick(dt, self._logical_w, ground_y,
                         self._bird.x, self._on_score)

        if self._bird.hits_ceiling_or_ground(ground_y):
            self._die()
        elif self._pipes.check_collision(self._bird.x, self._bird.y, 15):
            self._die()
```

### Design-space scaling

The game is authored at a fixed `DESIGN_H` (e.g. 900px tall) and scaled to fit
the actual window with a `set_transform` matrix on the root scene:

```python
def resize(self, screen_w: float, screen_h: float):
    self._scale     = screen_h / DESIGN_H
    self._logical_w = screen_w / self._scale
    self.set_transform(mat(e11=self._scale, e22=self._scale))
```

### Input

```python
def tap(self):
    if self._state == IDLE:
        self._state = PLAYING
        self._hud.hide_message()
        self._bird.jump()
    elif self._state == PLAYING:
        self._bird.jump()
    elif self._state == DEAD and self._dead_timer > 0.9:
        self._reset()
```

**Key takeaways:**

- A `Scene` subclass *is* the game — no separate root needed.
- Layered sub-scenes (`Sky`, `CloudLayer`, `PipeLayer`, ...) give clean parallax.
- Velocity + gravity is just two lines per frame — no physics library required.
- Rotation/scale via `set_transform` on each `Shape` or `Scene`.

---

## Tetris (with pymunk)

Tetris uses pymunk **only for debris** — line-clear particles that fly apart
under gravity. The game grid itself is logical (a 2D array of cell types), not
physical.

!!! info "Source code"
    [kivy-thor-games/games/thor-tetris](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-tetris)

### Where pymunk fits in

```python
import pymunk


class Physics:
    """Thin wrapper around pymunk.Space — gravity-driven debris only."""

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 1200)

    def add(self, *objs):
        self.space.add(*objs)

    def step(self, dt: float):
        self.space.step(dt)
```

The board's logical grid handles piece movement, rotation, line detection. The
moment lines clear, the cleared cells become **pymunk bodies** that bounce off
the walls and fall away.

### Game scene structure

```python
class TetrisGame(Scene):
    def __init__(self, w: float, h: float):
        super().__init__()
        self._layout = Layout(w, h)

        # background gradient
        self._bg = Shape(); self.add(self._bg)
        self._draw_bg(self._layout)

        # subsystems
        self._physics = Physics()
        self._walls   = Walls(self._physics, self._layout)

        # game scene (board + pieces + debris)
        self._game_scene = Scene()
        self.add(self._game_scene)

        self._board  = Board(self._game_scene, self._layout)
        self._ghost  = GhostPiece(self._game_scene, self._layout)
        self._piece  = ActivePiece(self._game_scene, self._layout)
        self._debris = Debris(self._game_scene, self._physics, self._layout)

        self._hud    = Hud(self._layout)
```

### Per-frame tick

```python
def tick(self, dt: float):
    dt = min(dt, 0.05)

    self._physics.step(dt)        # step the pymunk space
    self._debris.update(dt)       # sync debris visuals from bodies

    if self._state != ST_PLAYING:
        return

    # drop timer, lock delay, ghost piece...
    self._drop_timer += dt
    if self._drop_timer >= self._drop_interval():
        self._drop_timer = 0.0
        self._piece.drop_row(self._board)
```

### Spawning debris from cleared lines

When `check_lines()` returns full rows, each cleared cell becomes a pymunk body
with a random impulse, paired with a thorvg `Shape` that follows it.

```python
class Debris(Scene):
    def __init__(self, canvas: Scene, physics: Physics, layout: Layout):
        super().__init__()
        canvas.add(self)
        self._physics   = physics
        self._particles = []

    def spawn(self, cleared_cells, layout):
        cell = layout.cell
        size = cell * 0.88
        rx   = cell * 0.12

        for r, c, piece_type in cleared_cells:
            x = layout.board_x + c * cell + cell / 2
            y = layout.board_y + (r - SPAWN_ROWS) * cell + cell / 2

            # pymunk body
            mass = 1.0
            moment = pymunk.moment_for_box(mass, (size, size))
            body = pymunk.Body(mass, moment)
            body.position = (x, y)
            pm_shape = pymunk.Poly.create_box(body, (size, size))
            pm_shape.elasticity = 0.3
            pm_shape.friction = 0.5
            self._physics.add(body, pm_shape)

            # random kick
            body.apply_impulse_at_local_point((
                random.uniform(-DEBRIS_IMPULSE_X, DEBRIS_IMPULSE_X),
                DEBRIS_IMPULSE_Y + random.uniform(-100, 100),
            ))
            body.angular_velocity = random.uniform(-8, 8)

            # thorvg visual — matches the original cell
            base = PIECE_COLORS[piece_type]
            shp = Shape()
            half = size / 2
            shp.append_rect(-half, -half, size, size, rx=rx, ry=rx)
            shp.set_fill_color(*base, 255)
            self.add(shp)

            self._particles.append(_Particle(body, pm_shape, shp,
                                             ttl=DEBRIS_LIFETIME))
```

### Syncing visuals to physics each frame

```python
def update(self, dt: float):
    dead = []
    for p in self._particles:
        p.ttl -= dt
        if p.ttl <= 0:
            dead.append(p)
            continue

        # copy pymunk position + angle → thorvg matrix
        x, y = p.body.position
        m = Matrix()
        c = math.cos(p.body.angle); s = math.sin(p.body.angle)
        m.e11 =  c; m.e12 = -s; m.e13 = x
        m.e21 =  s; m.e22 =  c; m.e23 = y
        p.shape.set_transform(m)

    for p in dead:
        self._physics.remove(p.body, p.pm_shape)
        self.remove(p.shape)
        self._particles.remove(p)
```

### Static walls

The arena walls are static pymunk segments — debris bounces off them on the way
down.

```python
class Walls:
    def __init__(self, physics: Physics, layout: Layout):
        body = physics.space.static_body
        x0, y0 = layout.board_x, layout.board_y
        x1     = x0 + layout.cols * layout.cell
        y1     = y0 + layout.rows * layout.cell

        for a, b in [
            ((x0, y0), (x0, y1)),       # left wall
            ((x1, y0), (x1, y1)),       # right wall
            ((x0, y1), (x1, y1)),       # floor
        ]:
            seg = pymunk.Segment(body, a, b, 1)
            seg.elasticity = 0.5
            physics.add(seg)
```

**Key takeaways:**

- Use pymunk **only where physics is the right tool** — particle effects,
  bouncing debris, ragdolls. Don't use it for grid logic.
- Keep the pymunk wrapper tiny — `Physics` is just `space` + `step` + `add`.
- Each debris particle pairs a pymunk body with a thorvg `Shape`; sync the
  shape's `set_transform` from `body.position` + `body.angle` each frame.
- The main game scene graph (`Board`, `ActivePiece`, `GhostPiece`) is pure
  thorvg — no physics in the hot path.

---

## Wiring a game into Kivy

Both games are pure thorvg scenes — to render with Kivy, use the
[`GlCanvas` guide](../guides/kivy-integration.md):

```python
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy_thor import GlCanvas
from thor_flappy import FlappyScene


class FlappyApp(App):
    def build(self):
        root = Widget()
        canvas = GlCanvas(size=Window.size)
        root.add_widget(canvas)

        scene = FlappyScene()
        canvas.add(scene)
        canvas.add(scene.hud)

        scene.resize(*Window.size)
        Window.bind(on_resize=lambda *a: scene.resize(*Window.size))
        Window.bind(on_key_down=lambda *a: scene.tap() if a[1] == 32 else None)

        Clock.schedule_interval(scene.tick, 0)
        return root


FlappyApp().run()
```

---

## More games in the collection

- **[Thor Flappy](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-flappy)** — Flappy Bird (no pymunk)
- **[Thor Tetris](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-tetris)** — Tetris with pymunk debris
- **[Thor Ballbreaker](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-ballbreaker)** — Brick breaker with full pymunk physics
- **[Thor Tempest Run](https://github.com/Py-Swift/kivy-thor-games/tree/master/games/thor-tempest-run)** — Endless runner
