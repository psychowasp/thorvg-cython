# Paint

`Paint` is the abstract base class for all drawable objects in thorvg-cython. Shapes, Pictures, Scenes, and Text all inherit from `Paint`.

## Common Methods

### Transforms

#### `translate(x, y)`
```python
def translate(self, x: float, y: float) -> Result
```
Move the paint by `(x, y)` pixels.

#### `rotate(degree)`
```python
def rotate(self, degree: float) -> Result
```
Rotate the paint by `degree` degrees (clockwise).

#### `scale(factor)`
```python
def scale(self, factor: float) -> Result
```
Scale the paint uniformly by `factor`.

#### `set_transform(m)`
```python
def set_transform(self, m: Matrix) -> Result
```
Apply a full 3×3 affine transform matrix.

```python
import math
angle = math.radians(45)
m = tvg.Matrix(
    e11=math.cos(angle), e12=-math.sin(angle), e13=200,
    e21=math.sin(angle), e22=math.cos(angle),  e23=150,
)
shape.set_transform(m)
```

#### `get_transform()`
```python
def get_transform(self) -> tuple[Result, Matrix]
```
Get the current transform matrix.

### Opacity

#### `set_opacity(opacity)`
```python
def set_opacity(self, opacity: int) -> Result
```
Set opacity (0 = invisible, 255 = fully opaque).

#### `get_opacity()`
```python
def get_opacity(self) -> tuple[Result, int]
```

### Visibility

#### `set_visible(visible)`
```python
def set_visible(self, visible: bool) -> Result
```

#### `get_visible()`
```python
def get_visible(self) -> bool
```

### Duplication

#### `duplicate()`
```python
def duplicate(self) -> Paint | None
```
Create a deep copy of the paint.

### Bounding Boxes

#### `get_aabb()`
```python
def get_aabb(self) -> tuple[Result, float, float, float, float]
```
Get the axis-aligned bounding box. Returns `(result, x, y, w, h)`.

#### `get_obb()`
```python
def get_obb(self) -> tuple[Result, list[Point]]
```
Get the oriented bounding box as 4 corner points.

### Hit Testing

#### `intersects(x, y, w, h)`
```python
def intersects(self, x: int, y: int, w: int, h: int) -> bool
```
Test if the paint intersects with the given rectangle.

### Masking

#### `set_mask_method(target, method)`
```python
def set_mask_method(self, target: Paint, method: int) -> Result
```
Apply a mask from `target` paint using the specified `MaskMethod`.

```python
mask = tvg.Shape()
mask.append_circle(200, 200, 100, 100)
mask.set_fill_color(255, 255, 255)

shape.set_mask_method(mask, tvg.MaskMethod.ALPHA)
```

#### `get_mask_method()`
```python
def get_mask_method(self) -> tuple[Result, MaskMethod]
```

### Clipping

#### `set_clip(clipper)`
```python
def set_clip(self, clipper: Paint) -> Result
```
Clip this paint to the bounds of `clipper`.

#### `get_clip()`
```python
def get_clip(self) -> Paint | None
```

### Blend Modes

#### `set_blend_method(method)`
```python
def set_blend_method(self, method: int) -> Result
```
Set the blend mode (see `BlendMethod` enum).

```python
shape.set_blend_method(tvg.BlendMethod.MULTIPLY)
```

### Hierarchy

#### `get_parent()`
```python
def get_parent(self) -> Paint | None
```
Get the parent scene/canvas that contains this paint.

#### `get_type()`
```python
def get_type(self) -> tuple[Result, TvgType]
```
Get the paint's type (`SHAPE`, `PICTURE`, `SCENE`, `TEXT`).

### Reference Counting

#### `ref()`
```python
def ref(self) -> int
```
Increment the reference count.

#### `deref(free=False)`
```python
def deref(self, free: bool = False) -> int
```
Decrement the reference count. If `free=True`, destroys when count reaches 0.

#### `get_ref()`
```python
def get_ref(self) -> int
```
Get the current reference count.
