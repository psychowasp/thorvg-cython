# cython: language_level=3
"""
VulkanCanvas — Vulkan/WebGPU-accelerated canvas for GPU rendering on macOS.

Wraps ThorVG's WebGPU canvas (tvg_wgcanvas_*), which uses Vulkan (via
MoltenVK on macOS) as its backend.

This module is compiled only when THORVG_GPU=vulkan at build time.
When Vulkan support is disabled, vulkan_canvas.py provides a stub.
"""
from libc.stdint cimport uint32_t, uintptr_t
from cpython.pycapsule cimport PyCapsule_GetPointer, PyCapsule_IsValid

cimport thorvg_cython.cthorvg as tvg
from thorvg_cython.thorvg cimport Canvas
from thorvg_cython.thorvg import Result


cdef class VulkanCanvas(Canvas):
    """Vulkan-accelerated canvas via ThorVG's WebGPU backend.

    On macOS, ThorVG uses MoltenVK to translate Vulkan calls to Metal.
    The caller must supply valid Vulkan/WebGPU object handles.

    Example::

        canvas = VulkanCanvas()
        canvas.target(device, instance, surface, width, height)
        canvas.add(shape)
        canvas.draw()
        canvas.sync()

    Args:
        engine_option: Engine quality option (default: Quality).
    """

    def __cinit__(self, int engine_option=1, bint create=True):
        if create:
            self._c = tvg.tvg_wgcanvas_create(<tvg.Tvg_Engine_Option>engine_option)
        else:
            self._c = NULL

    @staticmethod
    def from_capsule(object capsule):
        """Wrap an existing Tvg_Canvas handed over from Swift (Sulphur).

        Accepts a PyCapsule named "Tvg_Canvas" containing a live
        tvg_wgcanvas instance (as produced by CanvasBase.asCapsule()).
        No new canvas is created; the returned VulkanCanvas borrows the
        handle — the Swift side keeps ownership, so do NOT call
        ``destroy()`` on it from Python.

        Args:
            capsule: PyCapsule("Tvg_Canvas") wrapping a Tvg_Canvas pointer.

        Returns:
            VulkanCanvas bound to the existing canvas instance.
        """
        if not PyCapsule_IsValid(capsule, "Tvg_Canvas"):
            raise ValueError('expected a PyCapsule named "Tvg_Canvas"')
        cdef void* ptr = PyCapsule_GetPointer(capsule, "Tvg_Canvas")
        if ptr == NULL:
            raise ValueError("capsule contains a NULL Tvg_Canvas pointer")
        cdef VulkanCanvas canvas = VulkanCanvas(create=False)
        canvas._c = <tvg.Tvg_Canvas>ptr
        return canvas

    cpdef target(self, uintptr_t device, uintptr_t instance,
                 uintptr_t target_surface, uint32_t w, uint32_t h,
                 int cs=0, int target_type=0):
        """Set the Vulkan/WebGPU render target.

        Args:
            device:         VkDevice / WGPUDevice handle.
            instance:       VkInstance / WGPUInstance handle.
            target_surface: Render target (VkImage, WGPUSurface, etc.).
            w:              Render target width in pixels.
            h:              Render target height in pixels.
            cs:             Colorspace (default: ABGR8888).
            target_type:    Backend target type hint (0 = default).
        """
        return Result(tvg.tvg_wgcanvas_set_target(
            self._c,
            <void*>device,
            <void*>instance,
            <void*>target_surface,
            w, h,
            <tvg.Tvg_Colorspace>cs,
            target_type,
        ))

    def __repr__(self):
        return "VulkanCanvas()"
