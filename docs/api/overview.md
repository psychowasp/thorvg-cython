# API Overview

thorvg-cython exposes ThorVG's C API through Cython classes organized into logical groups.

## Module Import

```python
import thorvg_cython as tvg
```

## Class Hierarchy

```
Engine              — Global initialization / teardown
├── Canvas          — Abstract base for render targets
│   ├── SwCanvas    — Software rasterizer (CPU)
│   └── GlCanvas    — OpenGL GPU rasterizer
├── Paint           — Abstract base for drawable objects
│   ├── Shape       — Vector shapes (paths, rects, circles)
│   ├── Picture     — Image/SVG/Lottie loader
│   ├── Scene       — Group container with effects
│   └── Text        — Text rendering
├── Gradient        — Abstract base for gradients
│   ├── LinearGradient
│   └── RadialGradient
├── Animation       — Animation controller
│   └── LottieAnimation — Lottie-specific extensions
├── Saver           — Export paints/animations to files
├── Accessor        — ID generation utility
└── PixelBuffer     — Raw pixel storage (PEP 3118)
```

## Enumerations

| Enum | Purpose |
|------|---------|
| `Result` | Operation return codes |
| `Colorspace` | Pixel format (ABGR8888, ARGB8888, etc.) |
| `EngineOption` | Canvas quality/optimization hints |
| `MaskMethod` | Alpha/luma masking modes |
| `BlendMethod` | Porter-Duff and blend modes |
| `TvgType` | Paint type identification |
| `PathCommand` | Path segment types |
| `StrokeCap` | Stroke line cap styles |
| `StrokeJoin` | Stroke line join styles |
| `StrokeFill` | Gradient spread modes |
| `FillRule` | Fill rule (non-zero / even-odd) |
| `TextWrap` | Text wrapping modes |
| `FilterMethod` | Image filtering modes |

## Data Classes

| Class | Fields | Purpose |
|-------|--------|---------|
| `ColorStop` | `offset`, `r`, `g`, `b`, `a` | Gradient color stop |
| `Point` | `x`, `y` | 2D coordinate |
| `Matrix` | `e11`–`e33` | 3×3 affine transform matrix |
| `TextMetrics` | `ascent`, `descent`, `linegap`, `advance` | Font metrics |

## Return Convention

Most methods return a `Result` enum value. Compound getters return tuples:

```python
# Simple setter — returns Result
result = shape.set_fill_color(255, 0, 0)

# Compound getter — returns (Result, ...values)
result, r, g, b, a = shape.get_fill_color()
```

## Thread Safety

- Call `Engine(threads=N)` to enable multi-threaded rendering
- Each canvas instance should be used from a single thread
- Multiple canvases can render in parallel
