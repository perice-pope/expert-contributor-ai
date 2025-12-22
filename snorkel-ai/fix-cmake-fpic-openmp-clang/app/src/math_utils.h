#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <vector>

// Parallel sum using OpenMP
double parallel_sum(const std::vector<double>& values);

// Parallel dot product using OpenMP
double parallel_dot_product(const std::vector<double>& a, const std::vector<double>& b);

#endif // MATH_UTILS_H

