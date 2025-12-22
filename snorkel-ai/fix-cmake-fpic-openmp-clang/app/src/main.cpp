#include "math_utils.h"
#include <iostream>
#include <vector>
#include <cassert>

int main() {
    // Test parallel sum
    std::vector<double> values = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0};
    double sum = parallel_sum(values);
    double expected_sum = 36.0;
    
    std::cout << "Sum: " << sum << " (expected: " << expected_sum << ")" << std::endl;
    assert(std::abs(sum - expected_sum) < 1e-9);
    
    // Test parallel dot product
    std::vector<double> a = {1.0, 2.0, 3.0};
    std::vector<double> b = {4.0, 5.0, 6.0};
    double dot = parallel_dot_product(a, b);
    double expected_dot = 32.0; // 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
    
    std::cout << "Dot product: " << dot << " (expected: " << expected_dot << ")" << std::endl;
    assert(std::abs(dot - expected_dot) < 1e-9);
    
    std::cout << "All tests passed!" << std::endl;
    return 0;
}

