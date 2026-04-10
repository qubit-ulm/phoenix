#ifndef PHOENIX_CUDA_SUPPORT_H
#define PHOENIX_CUDA_SUPPORT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

const char *phoenix_cuda_support_last_error(void);

int coeff_zero_f32(uintptr_t arr, size_t size);
int coeff_copy_f32(uintptr_t dst, uintptr_t src, size_t size);
int coeff_linop_f32(uintptr_t r, float a, uintptr_t x, int has_a, float b, uintptr_t y, int has_b, int has_y, size_t size, int inplace);
int coeff_zero_f64(uintptr_t arr, size_t size);
int coeff_copy_f64(uintptr_t dst, uintptr_t src, size_t size);
int coeff_linop_f64(uintptr_t r, double a, uintptr_t x, int has_a, double b, uintptr_t y, int has_b, int has_y, size_t size, int inplace);
int coeff_zero_i32(uintptr_t arr, size_t size);
int coeff_copy_i32(uintptr_t dst, uintptr_t src, size_t size);
int coeff_linop_i32(uintptr_t r, int32_t a, uintptr_t x, int has_a, int32_t b, uintptr_t y, int has_b, int has_y, size_t size, int inplace);
int coeff_zero_i64(uintptr_t arr, size_t size);
int coeff_copy_i64(uintptr_t dst, uintptr_t src, size_t size);
int coeff_linop_i64(uintptr_t r, int64_t a, uintptr_t x, int has_a, int64_t b, uintptr_t y, int has_b, int has_y, size_t size, int inplace);

#ifdef __cplusplus
}
#endif

#endif
