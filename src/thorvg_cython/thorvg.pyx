# cython: language_level=3
"""
ThorVG Cython wrapper — direct C-level binding (no ctypes overhead).
Every public class is a single ``cdef class`` importable from Python.
"""
from libc.stdint cimport uint8_t, uint16_t, uint32_t, int32_t, uintptr_t
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memset
from cpython.pycapsule cimport PyCapsule_New

cimport thorvg_cython.cthorvg as tvg

from enum import IntEnum

# ═══════════════════════════════════════════════════════════════════
#  Enumerations  (pure-Python IntEnum — pickle-able & inspectable)
# ═══════════════════════════════════════════════════════════════════

class Result(IntEnum):
    SUCCESS = 0
    INVALID_ARGUMENT = 1
    INSUFFICIENT_CONDITION = 2
    FAILED_ALLOCATION = 3
    MEMORY_CORRUPTION = 4
    NOT_SUPPORTED = 5
    UNKNOWN = 255

class Colorspace(IntEnum):
    ABGR8888 = 0
    ARGB8888 = 1
    ABGR8888S = 2
    ARGB8888S = 3
    UNKNOWN = 255

class EngineOption(IntEnum):
    NONE = 0
    DEFAULT = 1
    SMART_RENDER = 2

class MaskMethod(IntEnum):
    NONE = 0
    ALPHA = 1
    INVERSE_ALPHA = 2
    LUMA = 3
    INVERSE_LUMA = 4
    ADD = 5
    SUBTRACT = 6
    INTERSECT = 7
    DIFFERENCE = 8
    LIGHTEN = 9
    DARKEN = 10

class BlendMethod(IntEnum):
    NORMAL = 0
    MULTIPLY = 1
    SCREEN = 2
    OVERLAY = 3
    DARKEN = 4
    LIGHTEN = 5
    COLORDODGE = 6
    COLORBURN = 7
    HARDLIGHT = 8
    SOFTLIGHT = 9
    DIFFERENCE = 10
    EXCLUSION = 11
    HUE = 12
    SATURATION = 13
    COLOR = 14
    LUMINOSITY = 15
    ADD = 16
    COMPOSITION = 255

class TvgType(IntEnum):
    UNDEF = 0
    SHAPE = 1
    SCENE = 2
    PICTURE = 3
    TEXT = 4
    LINEAR_GRAD = 10
    RADIAL_GRAD = 11

class PathCommand(IntEnum):
    CLOSE = 0
    MOVE_TO = 1
    LINE_TO = 2
    CUBIC_TO = 3

class StrokeCap(IntEnum):
    BUTT = 0
    ROUND = 1
    SQUARE = 2

class StrokeJoin(IntEnum):
    MITER = 0
    ROUND = 1
    BEVEL = 2

class StrokeFill(IntEnum):
    PAD = 0
    REFLECT = 1
    REPEAT = 2

class FillRule(IntEnum):
    NON_ZERO = 0
    EVEN_ODD = 1

class TextWrap(IntEnum):
    NONE = 0
    CHARACTER = 1
    WORD = 2
    SMART = 3
    ELLIPSIS = 4
    HYPHENATION = 5

class FilterMethod(IntEnum):
    BILINEAR = 0
    NEAREST = 1


# ═══════════════════════════════════════════════════════════════════
#  Helper data classes
# ═══════════════════════════════════════════════════════════════════

class ColorStop:
    __slots__ = ("offset", "r", "g", "b", "a")
    def __init__(self, float offset, int r, int g, int b, int a=255):
        self.offset = offset; self.r = r; self.g = g; self.b = b; self.a = a

class Point:
    __slots__ = ("x", "y")
    def __init__(self, float x, float y):
        self.x = x; self.y = y

class Matrix:
    __slots__ = ("e11","e12","e13","e21","e22","e23","e31","e32","e33")
    def __init__(self, float e11=1, float e12=0, float e13=0,
                       float e21=0, float e22=1, float e23=0,
                       float e31=0, float e32=0, float e33=1):
        self.e11=e11; self.e12=e12; self.e13=e13
        self.e21=e21; self.e22=e22; self.e23=e23
        self.e31=e31; self.e32=e32; self.e33=e33

class TextMetrics:
    __slots__ = ("ascent", "descent", "linegap", "advance")
    def __init__(self, float ascent=0, float descent=0, float linegap=0, float advance=0):
        self.ascent = ascent; self.descent = descent
        self.linegap = linegap; self.advance = advance


# ═══════════════════════════════════════════════════════════════════
#  PixelBuffer  (buffer-protocol pixel storage for zero-copy blitting)
# ═══════════════════════════════════════════════════════════════════

cdef class PixelBuffer:
    """
    Heap-allocated RGBA pixel buffer that implements the Python buffer
    protocol (:pep:`3118`).

    Frameworks like Kivy can blit directly from this object without an
    intermediate ``bytes`` copy::

        buf = PixelBuffer(800, 600, Colorspace.ARGB8888)
        canvas = SwCanvas()
        canvas.set_target_buffer(buf)
        # … add paints, draw, sync …
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
    """

    def __cinit__(self, uint32_t w, uint32_t h, int cs=0,
                  uint32_t stride=0):
        self._w = w
        self._h = h
        self._stride = stride if stride != 0 else w
        self._cs = cs
        self._nbytes = <Py_ssize_t>(self._stride * h * sizeof(uint32_t))
        self._data = <uint32_t*>malloc(self._nbytes)
        if self._data == NULL:
            raise MemoryError("Failed to allocate pixel buffer")
        memset(self._data, 0, self._nbytes)
        self._shape[0]   = self._nbytes
        self._strides[0] = 1

    def __dealloc__(self):
        if self._data != NULL:
            free(self._data)
            self._data = NULL

    # ---- buffer protocol ------------------------------------------------

    def __getbuffer__(self, Py_buffer *buf, int flags):
        buf.buf        = <void*>self._data
        buf.len        = self._nbytes
        buf.readonly   = 0
        buf.format     = "B"          # unsigned bytes
        buf.ndim       = 1
        buf.shape      = self._shape
        buf.strides    = self._strides
        buf.suboffsets = NULL
        buf.itemsize   = 1
        buf.obj        = self          # prevent GC while view alive

    def __releasebuffer__(self, Py_buffer *buf):
        pass

    # ---- convenience API ------------------------------------------------

    @property
    def width(self):
        return self._w

    @property
    def height(self):
        return self._h

    @property
    def stride(self):
        return self._stride

    @property
    def colorspace(self):
        return Colorspace(self._cs)

    @property
    def nbytes(self):
        return self._nbytes

    @property
    def ptr(self):
        """Raw pointer as int — for advanced / interop use."""
        return <unsigned long>self._data

    cpdef clear(self):
        """Zero out all pixels."""
        memset(self._data, 0, self._nbytes)

    def __len__(self):
        return self._nbytes

    def __repr__(self):
        return (f"PixelBuffer({self._w}x{self._h}, "
                f"cs={Colorspace(self._cs).name}, "
                f"{self._nbytes} bytes)")


# ═══════════════════════════════════════════════════════════════════
#  Internal helpers  (cdef — not visible from Python)
# ═══════════════════════════════════════════════════════════════════

cdef inline int _check(tvg.Tvg_Result r) except -1:
    if r != tvg.TVG_RESULT_SUCCESS:
        raise RuntimeError(f"ThorVG error: {Result(r).name} ({r})")
    return 0

cdef inline tvg.Tvg_Matrix _mat_to_c(m):
    cdef tvg.Tvg_Matrix cm
    cm.e11 = m.e11; cm.e12 = m.e12; cm.e13 = m.e13
    cm.e21 = m.e21; cm.e22 = m.e22; cm.e23 = m.e23
    cm.e31 = m.e31; cm.e32 = m.e32; cm.e33 = m.e33
    return cm

cdef inline object _mat_from_c(tvg.Tvg_Matrix cm):
    return Matrix(cm.e11, cm.e12, cm.e13,
                  cm.e21, cm.e22, cm.e23,
                  cm.e31, cm.e32, cm.e33)


# ═══════════════════════════════════════════════════════════════════
#  Engine  (plain class — no C handle, just init/term)
# ═══════════════════════════════════════════════════════════════════

class Engine:
    def __init__(self, unsigned int threads=0):
        self.threads = threads
        self._result = <int>tvg.tvg_engine_init(threads)
        self._termed = False

    def __del__(self):
        if not self._termed:
            tvg.tvg_engine_term()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._termed:
            tvg.tvg_engine_term()
            self._termed = True

    @property
    def init_result(self):
        return Result(self._result)

    def init(self, unsigned int threads=0):
        return Result(tvg.tvg_engine_init(threads))

    def term(self):
        return Result(tvg.tvg_engine_term())

    def version(self):
        cdef uint32_t major, minor, micro
        cdef const char* ver
        cdef tvg.Tvg_Result r = tvg.tvg_engine_version(&major, &minor, &micro, &ver)
        v = ver.decode("utf-8") if ver != NULL else None
        return Result(r), major, minor, micro, v


# ═══════════════════════════════════════════════════════════════════
#  Paint
# ═══════════════════════════════════════════════════════════════════

cdef class Paint:

    def __cinit__(self):
        self._p = NULL
        self._owned = True

    cdef void _set(self, tvg.Tvg_Paint p, bint owned=True):
        self._p = p
        self._owned = owned

    # -- reference counting --
    cpdef ref(self):
        return tvg.tvg_paint_ref(self._p)

    cpdef deref(self, bint free=False):
        return tvg.tvg_paint_unref(self._p, free)

    cpdef get_ref(self):
        return tvg.tvg_paint_get_ref(self._p)

    # -- native interop --
    def capsule(self):
        """PyCapsule("Tvg_Paint") wrapping this paint's raw handle — for
        handing scenes/paints to native hosts. No ownership transfer: the
        capsule is a borrowed view, keep this Paint alive while it's used."""
        if self._p == NULL:
            raise ValueError("paint handle is NULL")
        return PyCapsule_New(<void*>self._p, "Tvg_Paint", NULL)

    # -- visibility --
    cpdef set_visible(self, bint visible):
        return Result(tvg.tvg_paint_set_visible(self._p, visible))

    cpdef get_visible(self):
        return tvg.tvg_paint_get_visible(self._p)

    # -- transforms --
    cpdef scale(self, float factor):
        return Result(tvg.tvg_paint_scale(self._p, factor))

    cpdef rotate(self, float degree):
        return Result(tvg.tvg_paint_rotate(self._p, degree))

    cpdef translate(self, float x, float y):
        return Result(tvg.tvg_paint_translate(self._p, x, y))

    cpdef set_transform(self, m):
        cdef tvg.Tvg_Matrix cm = _mat_to_c(m)
        return Result(tvg.tvg_paint_set_transform(self._p, &cm))

    cpdef get_transform(self):
        cdef tvg.Tvg_Matrix cm
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_transform(self._p, &cm)
        return Result(r), _mat_from_c(cm)

    # -- opacity --
    cpdef set_opacity(self, uint8_t opacity):
        return Result(tvg.tvg_paint_set_opacity(self._p, opacity))

    cpdef get_opacity(self):
        cdef uint8_t opacity
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_opacity(self._p, &opacity)
        return Result(r), opacity

    # -- duplicate --
    cpdef duplicate(self):
        cdef tvg.Tvg_Paint dup = tvg.tvg_paint_duplicate(self._p)
        if dup == NULL:
            return None
        cdef Paint p = Paint()
        p._set(dup, True)
        return p

    # -- hit-test --
    cpdef intersects(self, int x, int y, int w, int h):
        return tvg.tvg_paint_intersects(self._p, x, y, w, h)

    # -- bounding boxes --
    cpdef get_aabb(self):
        cdef float x, y, w, h
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_aabb(self._p, &x, &y, &w, &h)
        return Result(r), x, y, w, h

    cpdef get_obb(self):
        cdef tvg.Tvg_Point pt4[4]
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_obb(self._p, pt4)
        pts = [Point(pt4[i].x, pt4[i].y) for i in range(4)]
        return Result(r), pts

    # -- masking --
    cpdef set_mask_method(self, Paint target, int method):
        return Result(tvg.tvg_paint_set_mask_method(
            self._p, target._p, <tvg.Tvg_Mask_Method>method))

    cpdef get_mask_method(self):
        cdef tvg.Tvg_Paint target = NULL
        # Zero-init: C API writes only 1 byte (MaskMethod is uint8_t)
        # into a 4-byte Tvg_Mask_Method via reinterpret_cast
        cdef tvg.Tvg_Mask_Method method = <tvg.Tvg_Mask_Method>0
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_mask_method(
            self._p, <tvg.Tvg_Paint>&target, &method)
        return Result(r), MaskMethod(method)

    # -- clipping --
    cpdef set_clip(self, Paint clipper):
        return Result(tvg.tvg_paint_set_clip(self._p, clipper._p))

    cpdef get_clip(self):
        cdef tvg.Tvg_Paint cp = tvg.tvg_paint_get_clip(self._p)
        if cp == NULL:
            return None
        cdef Paint p = Paint()
        p._set(cp, False)
        return p

    cpdef get_parent(self):
        cdef tvg.Tvg_Paint pp = tvg.tvg_paint_get_parent(self._p)
        if pp == NULL:
            return None
        cdef Paint p = Paint()
        p._set(pp, False)
        return p

    cpdef get_type(self):
        cdef tvg.Tvg_Type t
        cdef tvg.Tvg_Result r = tvg.tvg_paint_get_type(self._p, &t)
        return Result(r), TvgType(t)

    cpdef set_blend_method(self, int method):
        return Result(tvg.tvg_paint_set_blend_method(
            self._p, <tvg.Tvg_Blend_Method>method))

    cpdef _rel(self):
        return Result(tvg.tvg_paint_rel(self._p))


# ═══════════════════════════════════════════════════════════════════
#  Canvas
# ═══════════════════════════════════════════════════════════════════

cdef class Canvas:

    def __cinit__(self):
        self._c = NULL

    cdef void _set(self, tvg.Tvg_Canvas c):
        self._c = c

    cpdef destroy(self):
        return Result(tvg.tvg_canvas_destroy(self._c))

    cpdef add(self, Paint paint):
        return Result(tvg.tvg_canvas_add(self._c, paint._p))

    cpdef insert(self, Paint target, Paint at=None):
        cdef tvg.Tvg_Paint at_p = NULL
        if at is not None:
            at_p = at._p
        return Result(tvg.tvg_canvas_insert(self._c, target._p, at_p))

    cpdef remove(self, Paint paint=None):
        cdef tvg.Tvg_Paint pp = NULL
        if paint is not None:
            pp = paint._p
        return Result(tvg.tvg_canvas_remove(self._c, pp))

    cpdef update(self):
        return Result(tvg.tvg_canvas_update(self._c))

    cpdef draw(self, bint clear=True):
        return Result(tvg.tvg_canvas_draw(self._c, clear))

    cpdef sync(self):
        return Result(tvg.tvg_canvas_sync(self._c))

    cpdef set_viewport(self, int x, int y, int w, int h):
        return Result(tvg.tvg_canvas_set_viewport(self._c, x, y, w, h))


# ═══════════════════════════════════════════════════════════════════
#  Gradient
# ═══════════════════════════════════════════════════════════════════

cdef class Gradient:

    def __cinit__(self):
        self._g = NULL

    cdef void _set(self, tvg.Tvg_Gradient g):
        self._g = g

    cpdef set_color_stops(self, stops):
        cdef int n = len(stops)
        cdef tvg.Tvg_Color_Stop* cs = <tvg.Tvg_Color_Stop*>malloc(
            n * sizeof(tvg.Tvg_Color_Stop))
        if cs == NULL:
            raise MemoryError()
        try:
            for i in range(n):
                s = stops[i]
                cs[i].offset = s.offset
                cs[i].r = s.r; cs[i].g = s.g; cs[i].b = s.b; cs[i].a = s.a
            return Result(tvg.tvg_gradient_set_color_stops(self._g, cs, n))
        finally:
            free(cs)

    cpdef get_color_stops(self):
        cdef const tvg.Tvg_Color_Stop* cs = NULL
        cdef uint32_t cnt = 0
        cdef tvg.Tvg_Result r = tvg.tvg_gradient_get_color_stops(self._g, &cs, &cnt)
        out = [ColorStop(cs[i].offset, cs[i].r, cs[i].g, cs[i].b, cs[i].a)
               for i in range(cnt)]
        return Result(r), out

    cpdef set_spread(self, int spread):
        return Result(tvg.tvg_gradient_set_spread(
            self._g, <tvg.Tvg_Stroke_Fill>spread))

    cpdef get_spread(self):
        cdef tvg.Tvg_Stroke_Fill spread
        cdef tvg.Tvg_Result r = tvg.tvg_gradient_get_spread(self._g, &spread)
        return Result(r), StrokeFill(spread)

    cpdef set_transform(self, m):
        cdef tvg.Tvg_Matrix cm = _mat_to_c(m)
        return Result(tvg.tvg_gradient_set_transform(self._g, &cm))

    cpdef get_transform(self):
        cdef tvg.Tvg_Matrix cm
        cdef tvg.Tvg_Result r = tvg.tvg_gradient_get_transform(self._g, &cm)
        return Result(r), _mat_from_c(cm)

    cpdef get_type(self):
        cdef tvg.Tvg_Type t
        cdef tvg.Tvg_Result r = tvg.tvg_gradient_get_type(self._g, &t)
        return Result(r), TvgType(t)

    cpdef duplicate(self):
        cdef tvg.Tvg_Gradient dup = tvg.tvg_gradient_duplicate(self._g)
        if dup == NULL:
            return None
        cdef Gradient g = type(self).__new__(type(self))
        g._set(dup)
        return g

    cpdef _del(self):
        return Result(tvg.tvg_gradient_del(self._g))


cdef class LinearGradient(Gradient):
    def __cinit__(self, float x1=0, float y1=0, float x2=0, float y2=0):
        self._g = tvg.tvg_linear_gradient_new()
        if x1 != 0 or y1 != 0 or x2 != 0 or y2 != 0:
            tvg.tvg_linear_gradient_set(self._g, x1, y1, x2, y2)

    cpdef set(self, float x1, float y1, float x2, float y2):
        return Result(tvg.tvg_linear_gradient_set(self._g, x1, y1, x2, y2))

    cpdef get(self):
        cdef float x1, y1, x2, y2
        cdef tvg.Tvg_Result r = tvg.tvg_linear_gradient_get(
            self._g, &x1, &y1, &x2, &y2)
        return Result(r), x1, y1, x2, y2


cdef class RadialGradient(Gradient):
    def __cinit__(self, float cx=0, float cy=0, float radius=0,
                        float fx=0, float fy=0, float fr=0):
        self._g = tvg.tvg_radial_gradient_new()
        if cx != 0 or cy != 0 or radius != 0:
            tvg.tvg_radial_gradient_set(self._g, cx, cy, radius, fx, fy, fr)

    cpdef set(self, float cx, float cy, float r,
            float fx=0, float fy=0, float fr=0):
        return Result(tvg.tvg_radial_gradient_set(
            self._g, cx, cy, r, fx, fy, fr))

    cpdef get(self):
        cdef float cx, cy, r, fx, fy, fr
        cdef tvg.Tvg_Result rv = tvg.tvg_radial_gradient_get(
            self._g, &cx, &cy, &r, &fx, &fy, &fr)
        return Result(rv), cx, cy, r, fx, fy, fr


# ═══════════════════════════════════════════════════════════════════
#  Shape
# ═══════════════════════════════════════════════════════════════════

cdef class Shape(Paint):
    def __cinit__(self):
        self._p = tvg.tvg_shape_new()

    # -- path --
    cpdef reset(self):
        return Result(tvg.tvg_shape_reset(self._p))

    cpdef move_to(self, float x, float y):
        return Result(tvg.tvg_shape_move_to(self._p, x, y))

    cpdef line_to(self, float x, float y):
        return Result(tvg.tvg_shape_line_to(self._p, x, y))

    cpdef cubic_to(self, float cx1, float cy1, float cx2, float cy2,
                 float x, float y):
        return Result(tvg.tvg_shape_cubic_to(
            self._p, cx1, cy1, cx2, cy2, x, y))

    cpdef close(self):
        return Result(tvg.tvg_shape_close(self._p))

    cpdef append_rect(self, float x, float y, float w, float h,
                    float rx=0, float ry=0, bint cw=True):
        return Result(tvg.tvg_shape_append_rect(
            self._p, x, y, w, h, rx, ry, cw))

    cpdef append_circle(self, float cx, float cy, float rx, float ry,
                      bint cw=True):
        return Result(tvg.tvg_shape_append_circle(
            self._p, cx, cy, rx, ry, cw))

    cpdef append_path(self, commands, points):
        cdef int cmd_cnt = len(commands)
        cdef int pts_cnt = len(points)
        cdef tvg.Tvg_Path_Command* cmds = <tvg.Tvg_Path_Command*>malloc(
            cmd_cnt * sizeof(tvg.Tvg_Path_Command))
        cdef tvg.Tvg_Point* pts = <tvg.Tvg_Point*>malloc(
            pts_cnt * sizeof(tvg.Tvg_Point))
        if cmds == NULL or pts == NULL:
            free(cmds); free(pts)
            raise MemoryError()
        try:
            for i in range(cmd_cnt):
                cmds[i] = <tvg.Tvg_Path_Command>int(commands[i])
            for i in range(pts_cnt):
                pts[i].x = points[i].x if hasattr(points[i], 'x') else points[i][0]
                pts[i].y = points[i].y if hasattr(points[i], 'y') else points[i][1]
            return Result(tvg.tvg_shape_append_path(
                self._p, cmds, cmd_cnt, pts, pts_cnt))
        finally:
            free(cmds); free(pts)

    cpdef get_path(self):
        cdef const tvg.Tvg_Path_Command* cmds = NULL
        cdef uint32_t cmd_cnt = 0
        cdef const tvg.Tvg_Point* pts = NULL
        cdef uint32_t pts_cnt = 0
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_path(
            self._p, &cmds, &cmd_cnt, &pts, &pts_cnt)
        out_cmds = [PathCommand(cmds[i]) for i in range(cmd_cnt)]
        out_pts = [Point(pts[i].x, pts[i].y) for i in range(pts_cnt)]
        return Result(r), out_cmds, out_pts

    # -- stroke --
    cpdef set_stroke_width(self, float width):
        return Result(tvg.tvg_shape_set_stroke_width(self._p, width))

    cpdef get_stroke_width(self):
        cdef float w
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_width(self._p, &w)
        return Result(r), w

    cpdef set_stroke_color(self, uint8_t r, uint8_t g, uint8_t b,
                         uint8_t a=255):
        return Result(tvg.tvg_shape_set_stroke_color(self._p, r, g, b, a))

    cpdef get_stroke_color(self):
        cdef uint8_t r, g, b, a
        cdef tvg.Tvg_Result rv = tvg.tvg_shape_get_stroke_color(
            self._p, &r, &g, &b, &a)
        return Result(rv), r, g, b, a

    cpdef set_stroke_gradient(self, Gradient grad):
        return Result(tvg.tvg_shape_set_stroke_gradient(self._p, grad._g))

    cpdef get_stroke_gradient(self):
        cdef tvg.Tvg_Gradient g = NULL
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_gradient(
            self._p, &g)
        if g == NULL:
            return Result(r), None
        cdef Gradient gr = Gradient()
        gr._set(g)
        return Result(r), gr

    cpdef set_stroke_dash(self, pattern, float offset=0):
        cdef int n = len(pattern)
        cdef float* dp = <float*>malloc(n * sizeof(float))
        if dp == NULL:
            raise MemoryError()
        try:
            for i in range(n):
                dp[i] = pattern[i]
            return Result(tvg.tvg_shape_set_stroke_dash(
                self._p, dp, n, offset))
        finally:
            free(dp)

    cpdef get_stroke_dash(self):
        cdef const float* dp = NULL
        cdef uint32_t cnt = 0
        cdef float offset = 0
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_dash(
            self._p, &dp, &cnt, &offset)
        out = [dp[i] for i in range(cnt)]
        return Result(r), out, offset

    cpdef set_stroke_cap(self, int cap):
        return Result(tvg.tvg_shape_set_stroke_cap(
            self._p, <tvg.Tvg_Stroke_Cap>cap))

    cpdef get_stroke_cap(self):
        cdef tvg.Tvg_Stroke_Cap cap
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_cap(self._p, &cap)
        return Result(r), StrokeCap(cap)

    cpdef set_stroke_join(self, int join):
        return Result(tvg.tvg_shape_set_stroke_join(
            self._p, <tvg.Tvg_Stroke_Join>join))

    cpdef get_stroke_join(self):
        cdef tvg.Tvg_Stroke_Join join
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_join(self._p, &join)
        return Result(r), StrokeJoin(join)

    cpdef set_stroke_miterlimit(self, float ml):
        return Result(tvg.tvg_shape_set_stroke_miterlimit(self._p, ml))

    cpdef get_stroke_miterlimit(self):
        cdef float ml
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_stroke_miterlimit(
            self._p, &ml)
        return Result(r), ml

    cpdef set_trimpath(self, float begin, float end,
                     bint simultaneous=False):
        return Result(tvg.tvg_shape_set_trimpath(
            self._p, begin, end, simultaneous))

    # -- fill --
    cpdef set_fill_color(self, uint8_t r, uint8_t g, uint8_t b,
                       uint8_t a=255):
        return Result(tvg.tvg_shape_set_fill_color(self._p, r, g, b, a))

    cpdef get_fill_color(self):
        cdef uint8_t r, g, b, a
        cdef tvg.Tvg_Result rv = tvg.tvg_shape_get_fill_color(
            self._p, &r, &g, &b, &a)
        return Result(rv), r, g, b, a

    cpdef set_fill_rule(self, int rule):
        return Result(tvg.tvg_shape_set_fill_rule(
            self._p, <tvg.Tvg_Fill_Rule>rule))

    cpdef get_fill_rule(self):
        cdef tvg.Tvg_Fill_Rule rule
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_fill_rule(self._p, &rule)
        return Result(r), FillRule(rule)

    cpdef set_paint_order(self, bint stroke_first):
        return Result(tvg.tvg_shape_set_paint_order(self._p, stroke_first))

    cpdef set_gradient(self, Gradient grad):
        return Result(tvg.tvg_shape_set_gradient(self._p, grad._g))

    cpdef get_gradient(self):
        cdef tvg.Tvg_Gradient g = NULL
        cdef tvg.Tvg_Result r = tvg.tvg_shape_get_gradient(self._p, &g)
        if g == NULL:
            return Result(r), None
        cdef Gradient gr = Gradient()
        gr._set(g)
        return Result(r), gr


# ═══════════════════════════════════════════════════════════════════
#  Picture
# ═══════════════════════════════════════════════════════════════════

cdef class Picture(Paint):
    def __cinit__(self):
        # Subclass __cinit__ is called after parent __cinit__.
        # Only create new if not set by a factory (e.g. from Animation).
        if self._p == NULL:
            self._p = tvg.tvg_picture_new()

    @staticmethod
    cdef Picture _wrap(tvg.Tvg_Paint p, bint owned):
        """Internal factory — wrap an existing C pointer."""
        cdef Picture pic = Picture.__new__(Picture)
        pic._p = p
        pic._owned = owned
        return pic

    cpdef load(self, str path):
        cdef bytes b = path.encode("utf-8")
        return Result(tvg.tvg_picture_load(self._p, b))

    cpdef load_raw(self, unsigned long data_ptr, uint32_t w, uint32_t h,
                 int cs=0, bint copy=True):
        return Result(tvg.tvg_picture_load_raw(
            self._p, <const uint32_t*><void*>data_ptr, w, h,
            <tvg.Tvg_Colorspace>cs, copy))

    cpdef load_data(self, bytes data, str mimetype="", str rpath="",
                  bint copy=True):
        cdef const char* mt_c = NULL
        cdef const char* rp_c = NULL
        cdef bytes mt_b, rp_b
        if mimetype:
            mt_b = mimetype.encode("utf-8")
            mt_c = mt_b
        if rpath:
            rp_b = rpath.encode("utf-8")
            rp_c = rp_b
        return Result(tvg.tvg_picture_load_data(
            self._p, data, len(data), mt_c, rp_c, copy))

    cpdef set_size(self, float w, float h):
        return Result(tvg.tvg_picture_set_size(self._p, w, h))

    cpdef get_size(self):
        cdef float w, h
        cdef tvg.Tvg_Result r = tvg.tvg_picture_get_size(self._p, &w, &h)
        return Result(r), w, h

    cpdef set_origin(self, float x, float y):
        return Result(tvg.tvg_picture_set_origin(self._p, x, y))

    cpdef get_origin(self):
        cdef float x, y
        cdef tvg.Tvg_Result r = tvg.tvg_picture_get_origin(self._p, &x, &y)
        return Result(r), x, y

    cpdef get_paint(self, uint32_t id):
        cdef tvg.Tvg_Paint pp = tvg.tvg_picture_get_paint(self._p, id)
        if pp == NULL:
            return None
        cdef Paint p = Paint()
        p._set(pp, False)
        return p


# ═══════════════════════════════════════════════════════════════════
#  Scene
# ═══════════════════════════════════════════════════════════════════

cdef class Scene(Paint):
    def __cinit__(self):
        self._p = tvg.tvg_scene_new()

    cpdef add(self, Paint paint):
        return Result(tvg.tvg_scene_add(self._p, paint._p))

    cpdef insert(self, Paint target, Paint at=None):
        cdef tvg.Tvg_Paint at_p = NULL
        if at is not None:
            at_p = at._p
        return Result(tvg.tvg_scene_insert(self._p, target._p, at_p))

    cpdef remove(self, Paint paint=None):
        cdef tvg.Tvg_Paint pp = NULL
        if paint is not None:
            pp = paint._p
        return Result(tvg.tvg_scene_remove(self._p, pp))

    cpdef clear_effects(self):
        return Result(tvg.tvg_scene_clear_effects(self._p))

    cpdef add_effect_gaussian_blur(self, double sigma, int direction=0,
                                 int border=0, int quality=50):
        return Result(tvg.tvg_scene_add_effect_gaussian_blur(
            self._p, sigma, direction, border, quality))

    cpdef add_effect_drop_shadow(self, int r, int g, int b, int a,
                               double angle=0, double distance=0,
                               double sigma=0, int quality=50):
        return Result(tvg.tvg_scene_add_effect_drop_shadow(
            self._p, r, g, b, a, angle, distance, sigma, quality))

    cpdef add_effect_fill(self, int r, int g, int b, int a):
        return Result(tvg.tvg_scene_add_effect_fill(self._p, r, g, b, a))

    cpdef add_effect_tint(self, int black_r, int black_g, int black_b,
                        int white_r, int white_g, int white_b,
                        double intensity=1.0):
        return Result(tvg.tvg_scene_add_effect_tint(
            self._p, black_r, black_g, black_b,
            white_r, white_g, white_b, intensity))

    cpdef add_effect_tritone(self, int sr, int sg, int sb,
                           int mr, int mg, int mb,
                           int hr, int hg, int hb,
                           double blend=0.5):
        return Result(tvg.tvg_scene_add_effect_tritone(
            self._p, sr, sg, sb, mr, mg, mb, hr, hg, hb, blend))


# ═══════════════════════════════════════════════════════════════════
#  Text
# ═══════════════════════════════════════════════════════════════════

cdef class Text(Paint):
    def __cinit__(self):
        self._p = tvg.tvg_text_new()

    cpdef set_font(self, str name):
        cdef bytes b = name.encode("utf-8")
        return Result(tvg.tvg_text_set_font(self._p, b))

    cpdef set_size(self, float size):
        return Result(tvg.tvg_text_set_size(self._p, size))

    cpdef set_text(self, str utf8):
        cdef bytes b = utf8.encode("utf-8")
        return Result(tvg.tvg_text_set_text(self._p, b))

    cpdef align(self, float x, float y):
        return Result(tvg.tvg_text_align(self._p, x, y))

    cpdef layout(self, float w, float h):
        return Result(tvg.tvg_text_layout(self._p, w, h))

    cpdef wrap_mode(self, int mode):
        return Result(tvg.tvg_text_wrap_mode(
            self._p, <tvg.Tvg_Text_Wrap>mode))

    cpdef spacing(self, float letter, float line):
        return Result(tvg.tvg_text_spacing(self._p, letter, line))

    cpdef set_italic(self, float shear):
        return Result(tvg.tvg_text_set_italic(self._p, shear))

    cpdef set_outline(self, float width, uint8_t r, uint8_t g, uint8_t b):
        return Result(tvg.tvg_text_set_outline(self._p, width, r, g, b))

    cpdef set_color(self, uint8_t r, uint8_t g, uint8_t b):
        return Result(tvg.tvg_text_set_color(self._p, r, g, b))

    cpdef set_gradient(self, Gradient grad):
        return Result(tvg.tvg_text_set_gradient(self._p, grad._g))

    cpdef get_text_metrics(self):
        cdef tvg.Tvg_Text_Metrics m
        cdef tvg.Tvg_Result r = tvg.tvg_text_get_text_metrics(self._p, &m)
        return Result(r), TextMetrics(m.ascent, m.descent, m.linegap, m.advance)

    @staticmethod
    def font_load(str path):
        cdef bytes b = path.encode("utf-8")
        return Result(tvg.tvg_font_load(b))

    @staticmethod
    def font_load_data(str name, bytes data, str mimetype="",
                       bint copy=True):
        cdef bytes n = name.encode("utf-8")
        cdef const char* mt_c = NULL
        cdef bytes mt_b
        if mimetype:
            mt_b = mimetype.encode("utf-8")
            mt_c = mt_b
        return Result(tvg.tvg_font_load_data(n, data, len(data), mt_c, copy))

    @staticmethod
    def font_unload(str path):
        cdef bytes b = path.encode("utf-8")
        return Result(tvg.tvg_font_unload(b))


# ═══════════════════════════════════════════════════════════════════
#  Animation
# ═══════════════════════════════════════════════════════════════════

cdef class Animation:

    def __cinit__(self):
        self._a = tvg.tvg_animation_new()

    cpdef set_frame(self, float no):
        return Result(tvg.tvg_animation_set_frame(self._a, no))

    cpdef get_picture(self):
        cdef tvg.Tvg_Paint pp = tvg.tvg_animation_get_picture(self._a)
        return Picture._wrap(pp, False)

    cpdef get_frame(self):
        cdef float no
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_frame(self._a, &no)
        return Result(r), no

    cpdef get_total_frame(self):
        cdef float total
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_total_frame(
            self._a, &total)
        return Result(r), total

    cpdef get_duration(self):
        cdef float dur
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_duration(
            self._a, &dur)
        return Result(r), dur

    cpdef set_segment(self, float begin, float end):
        return Result(tvg.tvg_animation_set_segment(self._a, begin, end))

    cpdef get_segment(self):
        cdef float begin, end
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_segment(
            self._a, &begin, &end)
        return Result(r), begin, end

    cpdef _del(self):
        return Result(tvg.tvg_animation_del(self._a))


# ═══════════════════════════════════════════════════════════════════
#  LottieAnimation
# ═══════════════════════════════════════════════════════════════════

cdef class LottieAnimation(Animation):
    def __cinit__(self):
        # Override parent — use lottie-specific constructor
        self._a = tvg.tvg_lottie_animation_new()

    cpdef gen_slot(self, str slot):
        cdef bytes b = slot.encode("utf-8")
        return tvg.tvg_lottie_animation_gen_slot(self._a, b)

    cpdef apply_slot(self, uint32_t id):
        return Result(tvg.tvg_lottie_animation_apply_slot(self._a, id))

    cpdef del_slot(self, uint32_t id):
        return Result(tvg.tvg_lottie_animation_del_slot(self._a, id))

    cpdef set_marker(self, str marker):
        cdef bytes b = marker.encode("utf-8")
        return Result(tvg.tvg_lottie_animation_set_marker(self._a, b))

    cpdef get_markers_cnt(self):
        cdef uint32_t cnt
        cdef tvg.Tvg_Result r = tvg.tvg_lottie_animation_get_markers_cnt(
            self._a, &cnt)
        return Result(r), cnt

    cpdef get_marker(self, uint32_t idx):
        cdef const char* marker = NULL
        cdef tvg.Tvg_Result r = tvg.tvg_lottie_animation_get_marker(
            self._a, idx, &marker)
        name = marker.decode("utf-8") if marker != NULL else None
        return Result(r), name

    cpdef tween(self, float from_, float to, float progress):
        return Result(tvg.tvg_lottie_animation_tween(
            self._a, from_, to, progress))

    cpdef assign(self, str layer, uint32_t ix, str var, float val):
        cdef bytes lb = layer.encode("utf-8")
        cdef bytes vb = var.encode("utf-8")
        return Result(tvg.tvg_lottie_animation_assign(
            self._a, lb, ix, vb, val))

    cpdef set_quality(self, uint8_t value):
        return Result(tvg.tvg_lottie_animation_set_quality(self._a, value))


# ═══════════════════════════════════════════════════════════════════
#  Saver
# ═══════════════════════════════════════════════════════════════════

cdef class Saver:

    def __cinit__(self):
        self._s = tvg.tvg_saver_new()

    cpdef save_paint(self, Paint paint, str path, uint32_t quality=100):
        cdef bytes b = path.encode("utf-8")
        return Result(tvg.tvg_saver_save_paint(self._s, paint._p, b, quality))

    cpdef save_animation(self, Animation animation, str path,
                       uint32_t quality=100, uint32_t fps=0):
        cdef bytes b = path.encode("utf-8")
        return Result(tvg.tvg_saver_save_animation(
            self._s, animation._a, b, quality, fps))

    cpdef sync(self):
        return Result(tvg.tvg_saver_sync(self._s))

    cpdef _del(self):
        return Result(tvg.tvg_saver_del(self._s))


# ═══════════════════════════════════════════════════════════════════
#  Accessor
# ═══════════════════════════════════════════════════════════════════

cdef class Accessor:

    def __cinit__(self):
        self._acc = tvg.tvg_accessor_new()

    cpdef _del(self):
        return Result(tvg.tvg_accessor_del(self._acc))

    @staticmethod
    def generate_id(str name):
        cdef bytes b = name.encode("utf-8")
        return tvg.tvg_accessor_generate_id(b)

