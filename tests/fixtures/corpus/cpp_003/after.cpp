#include <vector>

namespace math {
int sum(std::vector<int> values) {
    int total = 0;
    for (int v : values) total += v;
    return total;
}
}
