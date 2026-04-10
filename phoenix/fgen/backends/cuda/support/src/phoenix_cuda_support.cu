#include "phoenix_cuda_support.h"

#include <cuda.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char PHOENIX_CUDA_SUPPORT_ERROR[512] = "";

const char *phoenix_cuda_support_last_error(void) {
    return PHOENIX_CUDA_SUPPORT_ERROR;
}

static int phoenix_cuda_support_fail(const char *message) {
    snprintf(PHOENIX_CUDA_SUPPORT_ERROR, sizeof(PHOENIX_CUDA_SUPPORT_ERROR), "%s", message);
    return 1;
}

static int phoenix_cuda_support_fail_cuda(const char *prefix, CUresult result) {
    const char *name = NULL;
    const char *message = NULL;
    cuGetErrorName(result, &name);
    cuGetErrorString(result, &message);
    snprintf(
        PHOENIX_CUDA_SUPPORT_ERROR,
        sizeof(PHOENIX_CUDA_SUPPORT_ERROR),
        "%s: %s (%s)",
        prefix,
        message != NULL ? message : "unknown CUDA driver error",
        name != NULL ? name : "unknown"
    );
    return 1;
}

static int phoenix_cuda_support_prepare(void) {
    CUcontext context = NULL;
    CUresult result = cuInit(0);
    if (result != CUDA_SUCCESS) {
        return phoenix_cuda_support_fail_cuda("cuInit failed", result);
    }
    result = cuCtxGetCurrent(&context);
    if (result != CUDA_SUCCESS) {
        return phoenix_cuda_support_fail_cuda("cuCtxGetCurrent failed", result);
    }
    if (context == NULL) {
        return phoenix_cuda_support_fail("no current CUDA context available");
    }
    return 0;
}

#define DEFINE_CUDA_BASIC_OPS(NAME, TYPE)                                       \
    int coeff_zero_##NAME(uintptr_t arr, size_t size) {                         \
        CUresult result;                                                         \
        if (arr == 0) {                                                          \
            return 0;                                                            \
        }                                                                        \
        if (phoenix_cuda_support_prepare() != 0) {                               \
            return 1;                                                            \
        }                                                                        \
        result = cuMemsetD8((CUdeviceptr)arr, 0, size * sizeof(TYPE));           \
        if (result != CUDA_SUCCESS) {                                            \
            return phoenix_cuda_support_fail_cuda("cuMemsetD8 failed", result); \
        }                                                                        \
        return 0;                                                                \
    }                                                                            \
                                                                                 \
    int coeff_copy_##NAME(uintptr_t dst, uintptr_t src, size_t size) {           \
        CUresult result;                                                         \
        if (dst == 0 || src == 0) {                                              \
            return phoenix_cuda_support_fail("coeff_copy received null pointer");\
        }                                                                        \
        if (phoenix_cuda_support_prepare() != 0) {                               \
            return 1;                                                            \
        }                                                                        \
        result = cuMemcpyDtoD((CUdeviceptr)dst, (CUdeviceptr)src, size * sizeof(TYPE));\
        if (result != CUDA_SUCCESS) {                                            \
            return phoenix_cuda_support_fail_cuda("cuMemcpyDtoD failed", result);\
        }                                                                        \
        return 0;                                                                \
    }                                                                            \
                                                                                 \
    int coeff_linop_##NAME(                                                      \
        uintptr_t r, TYPE a, uintptr_t x, int has_a, TYPE b, uintptr_t y,        \
        int has_b, int has_y, size_t size, int inplace                           \
    ) {                                                                          \
        CUresult result;                                                         \
        TYPE *host_r = NULL;                                                     \
        TYPE *host_x = NULL;                                                     \
        TYPE *host_y = NULL;                                                     \
        if (r == 0) {                                                            \
            return 0;                                                            \
        }                                                                        \
        if (phoenix_cuda_support_prepare() != 0) {                               \
            return 1;                                                            \
        }                                                                        \
        host_r = (TYPE *)malloc(size * sizeof(TYPE));                            \
        if (host_r == NULL) {                                                    \
            return phoenix_cuda_support_fail("malloc failed for host_r");       \
        }                                                                        \
        if (inplace) {                                                           \
            result = cuMemcpyDtoH(host_r, (CUdeviceptr)r, size * sizeof(TYPE));  \
            if (result != CUDA_SUCCESS) {                                        \
                free(host_r);                                                    \
                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\
            }                                                                    \
        } else {                                                                 \
            memset(host_r, 0, size * sizeof(TYPE));                              \
        }                                                                        \
        if (x != 0) {                                                            \
            host_x = (TYPE *)malloc(size * sizeof(TYPE));                        \
            if (host_x == NULL) {                                                \
                free(host_r);                                                    \
                return phoenix_cuda_support_fail("malloc failed for host_x");   \
            }                                                                    \
            result = cuMemcpyDtoH(host_x, (CUdeviceptr)x, size * sizeof(TYPE));  \
            if (result != CUDA_SUCCESS) {                                        \
                free(host_x);                                                    \
                free(host_r);                                                    \
                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\
            }                                                                    \
        }                                                                        \
        if (has_y && y != 0) {                                                   \
            host_y = (TYPE *)malloc(size * sizeof(TYPE));                        \
            if (host_y == NULL) {                                                \
                free(host_x);                                                    \
                free(host_r);                                                    \
                return phoenix_cuda_support_fail("malloc failed for host_y");   \
            }                                                                    \
            result = cuMemcpyDtoH(host_y, (CUdeviceptr)y, size * sizeof(TYPE));  \
            if (result != CUDA_SUCCESS) {                                        \
                free(host_y);                                                    \
                free(host_x);                                                    \
                free(host_r);                                                    \
                return phoenix_cuda_support_fail_cuda("cuMemcpyDtoH failed", result);\
            }                                                                    \
        }                                                                        \
        for (size_t i = 0; i < size; ++i) {                                      \
            TYPE value = inplace ? host_r[i] : (TYPE)0;                          \
            if (host_x != NULL) {                                                \
                value += has_a ? (a * host_x[i]) : host_x[i];                    \
            }                                                                    \
            if (host_y != NULL) {                                                \
                value += has_b ? (b * host_y[i]) : host_y[i];                    \
            } else if (has_b) {                                                  \
                value += b;                                                      \
            }                                                                    \
            host_r[i] = value;                                                   \
        }                                                                        \
        result = cuMemcpyHtoD((CUdeviceptr)r, host_r, size * sizeof(TYPE));      \
        free(host_y);                                                            \
        free(host_x);                                                            \
        free(host_r);                                                            \
        if (result != CUDA_SUCCESS) {                                            \
            return phoenix_cuda_support_fail_cuda("cuMemcpyHtoD failed", result);\
        }                                                                        \
        return 0;                                                                \
    }

DEFINE_CUDA_BASIC_OPS(f32, float)
DEFINE_CUDA_BASIC_OPS(f64, double)
DEFINE_CUDA_BASIC_OPS(i32, int32_t)
DEFINE_CUDA_BASIC_OPS(i64, int64_t)
