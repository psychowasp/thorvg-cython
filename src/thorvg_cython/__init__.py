"""thorvg-cython — Cython bindings for the ThorVG C API."""

__version__ = "0.0.6"

from .thorvg import (  # noqa: F401
    # Enums
    Result,
    Colorspace,
    EngineOption,
    MaskMethod,
    BlendMethod,
    TvgType,
    PathCommand,
    StrokeCap,
    StrokeJoin,
    StrokeFill,
    FillRule,
    TextWrap,
    FilterMethod,
    # Data classes
    ColorStop,
    Point,
    Matrix,
    TextMetrics,
    # Buffer
    PixelBuffer,
    # Core
    Engine,
    Canvas,
    Paint,
    Shape,
    Picture,
    Scene,
    Text,
    # Gradients
    Gradient,
    LinearGradient,
    RadialGradient,
    # Animation
    Animation,
    LottieAnimation,
    # Utilities
    Saver,
    Accessor,
)

from .sw_canvas import SwCanvas  # noqa: F401
from .gl_canvas import GlCanvas  # noqa: F401
