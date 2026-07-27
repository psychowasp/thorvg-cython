"""Type stubs for thorvg_cython.vulkan_canvas."""

from __future__ import annotations

from .thorvg import Canvas, Result


class VulkanCanvas(Canvas):
    """Vulkan-accelerated canvas via ThorVG's WebGPU/MoltenVK backend."""

    def __init__(self, engine_option: int = 1, create: bool = True) -> None: ...
    @staticmethod
    def from_capsule(capsule: object) -> VulkanCanvas: ...
    def target(
        self,
        device: int,
        instance: int,
        target_surface: int,
        w: int,
        h: int,
        cs: int = 0,
        target_type: int = 0,
    ) -> Result: ...
    def __repr__(self) -> str: ...
