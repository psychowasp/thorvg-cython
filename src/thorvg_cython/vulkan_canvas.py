class VulkanCanvas:
    """Stub: thorvg-cython was not built with Vulkan support."""

    def __init__(self, engine_option: int = 1, create: bool = True) -> None:
        raise RuntimeError(
            "VulkanCanvas is not available: thorvg-cython was built without "
            "Vulkan GPU support. Rebuild with THORVG_GPU=vulkan."
        )

    @staticmethod
    def from_capsule(capsule: object) -> "VulkanCanvas":
        raise RuntimeError(
            "VulkanCanvas is not available: thorvg-cython was built without "
            "Vulkan GPU support. Rebuild with THORVG_GPU=vulkan."
        )
