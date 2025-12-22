#include "math_utils.h"
#include <omp.h>
#include <numeric>

double parallel_sum(const std::vector<double>& values) {
    double sum = 0.0;
    
    #pragma omp parallel for reduction(+:sum)
    for (size_t i = 0; i < values.size(); ++i) {
        sum += values[i];
    }
    
    return sum;
}

double parallel_dot_product(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size()) {
        return 0.0;
    }
    
    double result = 0.0;
    
    #pragma omp parallel for reduction(+:result)
    for (size_t i = 0; i < a.size(); ++i) {
        result += a[i] * b[i];
    }
    
    return result;
}

