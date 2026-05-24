# Text

`Text` renders text using loaded TrueType fonts.

## Constructor

```python
text = tvg.Text()
```

## Font Management

Before rendering text, you must load a font:

### `Text.font_load(path)` (static)
```python
@staticmethod
def font_load(path: str) -> Result
```
Load a font file (.ttf, .otf).

### `Text.font_load_data(name, data, mimetype="", copy=True)` (static)
```python
@staticmethod
def font_load_data(name: str, data: bytes,
                   mimetype: str = "", copy: bool = True) -> Result
```
Load a font from in-memory bytes.

### `Text.font_unload(path)` (static)
```python
@staticmethod
def font_unload(path: str) -> Result
```
Unload a previously loaded font.

## Text Properties

### `set_font(name)`
```python
def set_font(self, name: str) -> Result
```
Set the font by name (as registered via `font_load`).

### `set_size(size)`
```python
def set_size(self, size: float) -> Result
```
Set the font size in pixels.

### `set_text(utf8)`
```python
def set_text(self, utf8: str) -> Result
```
Set the text content.

### `set_color(r, g, b)`
```python
def set_color(self, r: int, g: int, b: int) -> Result
```
Set the text fill color.

### `set_gradient(grad)`
```python
def set_gradient(self, grad: Gradient) -> Result
```
Fill text with a gradient.

## Layout

### `align(x, y)`
```python
def align(self, x: float, y: float) -> Result
```
Set text alignment offsets.

### `layout(w, h)`
```python
def layout(self, w: float, h: float) -> Result
```
Set the text layout bounds for wrapping.

### `wrap_mode(mode)`
```python
def wrap_mode(self, mode: int) -> Result
```
Set the text wrapping mode. Options:

- `TextWrap.NONE` — No wrapping
- `TextWrap.CHARACTER` — Wrap at character boundaries
- `TextWrap.WORD` — Wrap at word boundaries
- `TextWrap.SMART` — Smart wrapping
- `TextWrap.ELLIPSIS` — Truncate with ellipsis
- `TextWrap.HYPHENATION` — Wrap with hyphenation

### `spacing(letter, line)`
```python
def spacing(self, letter: float, line: float) -> Result
```
Set letter and line spacing.

## Styling

### `set_italic(shear)`
```python
def set_italic(self, shear: float) -> Result
```
Apply italic shear. Typically `0.2`–`0.4`.

### `set_outline(width, r, g, b)`
```python
def set_outline(self, width: float, r: int, g: int, b: int) -> Result
```
Add a text outline/stroke.

## Metrics

### `get_text_metrics()`
```python
def get_text_metrics(self) -> tuple[Result, TextMetrics]
```
Get font metrics for the current text.

```python
result, metrics = text.get_text_metrics()
print(f"Ascent: {metrics.ascent}, Descent: {metrics.descent}")
print(f"Line gap: {metrics.linegap}, Advance: {metrics.advance}")
```

## Example

```python
import thorvg_cython as tvg

with tvg.Engine(threads=2):
    canvas = tvg.SwCanvas(400, 200)

    # Load font
    tvg.Text.font_load("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

    # Create text
    text = tvg.Text()
    text.set_font("DejaVuSans")
    text.set_size(36.0)
    text.set_text("Hello, ThorVG!")
    text.set_color(255, 255, 255)
    text.translate(20, 80)

    canvas.add(text)
    canvas.draw()
    canvas.sync()
```
