#include "phoenix_c_support.h"

#define DEFINE_ZERO(NAME, TYPE)                                        \
    void phoenix_zero_##NAME(TYPE *buffer, int32_t size) {             \
        for (int32_t idx = 0; idx < size; ++idx) {                      \
            buffer[idx] = (TYPE)0;                                      \
        }                                                               \
    }

#define DEFINE_ZERO_COPY_LINOP(NAME, TYPE)                               \
    void coeff_zero_##NAME(TYPE *arr, size_t size) {                    \
        for (size_t i = 0; i < size; ++i) {                              \
            arr[i] = (TYPE)0;                                            \
        }                                                                \
    }                                                                    \
                                                                         \
    void coeff_copy_##NAME(TYPE *dst, const TYPE *src, size_t size) {    \
        for (size_t i = 0; i < size; ++i) {                              \
            dst[i] = src[i];                                             \
        }                                                                \
    }                                                                    \
                                                                         \
    void coeff_linop_##NAME(                                             \
        TYPE *r,                                                         \
        TYPE a,                                                          \
        const TYPE *x,                                                   \
        int has_a,                                                       \
        TYPE b,                                                          \
        const TYPE *y,                                                   \
        int has_b,                                                       \
        int has_y,                                                       \
        size_t size,                                                     \
        int inplace                                                      \
    ) {                                                                  \
        for (size_t i = 0; i < size; ++i) {                              \
            TYPE value = inplace ? r[i] : (TYPE)0;                       \
            if (x != NULL) {                                             \
                value += has_a ? (a * x[i]) : x[i];                      \
            }                                                            \
            if (has_y && y != NULL) {                                    \
                value += has_b ? (b * y[i]) : y[i];                      \
            } else if (has_b) {                                          \
                value += b;                                              \
            }                                                            \
            r[i] = value;                                                \
        }                                                                \
    }

DEFINE_ZERO(f32, float)
DEFINE_ZERO(f64, double)
DEFINE_ZERO(i32, int32_t)
DEFINE_ZERO(i64, int64_t)

DEFINE_ZERO_COPY_LINOP(f32, float)
DEFINE_ZERO_COPY_LINOP(f64, double)
DEFINE_ZERO_COPY_LINOP(i32, int32_t)
DEFINE_ZERO_COPY_LINOP(i64, int64_t)
