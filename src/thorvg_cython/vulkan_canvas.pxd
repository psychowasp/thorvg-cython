# cython: language_level=3
from libc.stdint cimport uint32_t, uintptr_t
from thorvg_cython.thorvg cimport Canvas


cdef class VulkanCanvas(Canvas):
    cpdef target(self, uintptr_t device, uintptr_t instance,
                 uintptr_t target_surface, uint32_t w, uint32_t h,
                 int cs=*, int target_type=*)
