#ifndef PHOENIX_C_SUPPORT_H
#define PHOENIX_C_SUPPORT_H

#include <stddef.h>
#include <stdint.h>

void phoenix_zero_f32(float *buffer, int32_t size);
void phoenix_zero_f64(double *buffer, int32_t size);
void phoenix_zero_i32(int32_t *buffer, int32_t size);
void phoenix_zero_i64(int64_t *buffer, int32_t size);

void coeff_zero_f32(float *arr, size_t size);
void coeff_copy_f32(float *dst, const float *src, size_t size);
void coeff_linop_f32(float *r, float a, const float *x, int has_a, float b, const float *y, int has_b, int has_y, size_t size, int inplace);
void coeff_zero_f64(double *arr, size_t size);
void coeff_copy_f64(double *dst, const double *src, size_t size);
void coeff_linop_f64(double *r, double a, const double *x, int has_a, double b, const double *y, int has_b, int has_y, size_t size, int inplace);
void coeff_zero_i32(int32_t *arr, size_t size);
void coeff_copy_i32(int32_t *dst, const int32_t *src, size_t size);
void coeff_linop_i32(int32_t *r, int32_t a, const int32_t *x, int has_a, int32_t b, const int32_t *y, int has_b, int has_y, size_t size, int inplace);
void coeff_zero_i64(int64_t *arr, size_t size);
void coeff_copy_i64(int64_t *dst, const int64_t *src, size_t size);
void coeff_linop_i64(int64_t *r, int64_t a, const int64_t *x, int has_a, int64_t b, const int64_t *y, int has_b, int has_y, size_t size, int inplace);

#endif
