# Scene

`Scene` groups multiple paints into a single entity that can be transformed and have effects applied collectively.

## Constructor

```python
scene = tvg.Scene()
```

## Managing Children

### `add(paint)`
```python
def add(self, paint: Paint) -> Result
```
Add a paint to the scene.

### `insert(target, at=None)`
```python
def insert(self, target: Paint, at: Paint | None = None) -> Result
```
Insert at a specific position.

### `remove(paint=None)`
```python
def remove(self, paint: Paint | None = None) -> Result
```
Remove a paint. If `None`, removes all children.

## Effects

Scenes support post-processing effects applied to all their children.

### `add_effect_gaussian_blur(sigma, direction=0, border=0, quality=50)`
```python
def add_effect_gaussian_blur(self, sigma: float, direction: int = 0,
                             border: int = 0, quality: int = 50) -> Result
```
Apply a Gaussian blur effect.

| Parameter | Description |
|-----------|-------------|
| `sigma` | Blur radius |
| `direction` | 0=both, 1=horizontal, 2=vertical |
| `border` | 0=default, 1=duplicate edge pixels |
| `quality` | 0–100, higher = better quality |

```python
scene = tvg.Scene()
scene.add(shape1)
scene.add(shape2)
scene.add_effect_gaussian_blur(5.0)
canvas.add(scene)
```

### `add_effect_drop_shadow(r, g, b, a, angle=0, distance=0, sigma=0, quality=50)`
```python
def add_effect_drop_shadow(self, r: int, g: int, b: int, a: int,
                           angle: float = 0, distance: float = 0,
                           sigma: float = 0, quality: int = 50) -> Result
```
Apply a drop shadow effect.

```python
scene.add_effect_drop_shadow(0, 0, 0, 128, angle=45, distance=10, sigma=5)
```

### `add_effect_fill(r, g, b, a)`
```python
def add_effect_fill(self, r: int, g: int, b: int, a: int) -> Result
```
Fill the entire scene bounds with a solid color.

### `add_effect_tint(black_r, black_g, black_b, white_r, white_g, white_b, intensity=1.0)`
```python
def add_effect_tint(self, black_r: int, black_g: int, black_b: int,
                    white_r: int, white_g: int, white_b: int,
                    intensity: float = 1.0) -> Result
```
Apply a tint effect mapping shadows to one color and highlights to another.

### `add_effect_tritone(sr, sg, sb, mr, mg, mb, hr, hg, hb, blend=0.5)`
```python
def add_effect_tritone(self, sr: int, sg: int, sb: int,
                       mr: int, mg: int, mb: int,
                       hr: int, hg: int, hb: int,
                       blend: float = 0.5) -> Result
```
Apply a three-tone color mapping (shadows, midtones, highlights).

### `clear_effects()`
```python
def clear_effects(self) -> Result
```
Remove all effects from the scene.

## Example: Game Scene Graph

```python
import thorvg_cython as tvg

tvg.Engine(threads=4)
canvas = tvg.GlCanvas()
canvas.target(0, 0, 0, fbo_id, 1280, 720)

# Root scene
root = tvg.Scene()
canvas.add(root)

# Background layer
bg = tvg.Shape()
bg.append_rect(0, 0, 1280, 720)
bg.set_fill_color(10, 10, 20)
root.add(bg)

# Game entities layer
game_scene = tvg.Scene()
root.add(game_scene)

# Player
player = tvg.Shape()
player.move_to(20, 0)
player.line_to(-14, -12)
player.line_to(-8, 0)
player.line_to(-14, 12)
player.close()
player.set_stroke_width(2.0)
player.set_stroke_color(0, 255, 200)
game_scene.add(player)

# HUD layer (on top)
hud_scene = tvg.Scene()
canvas.add(hud_scene)

canvas.draw()
canvas.sync()
```
