#include <iostream>
#include "cpp/calculator.h"

int main() {
    Calculator calc;
    int result = calc.add(10, 20);
    std::cout << "Result: " << result << std::endl;
    return 0;
}

