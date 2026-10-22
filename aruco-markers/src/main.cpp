#include "aruco.h"

#include <cstdio>

int main() {
    std::vector<Marker> dictionary = build_dictionary(5);
    for (const Marker &marker : dictionary) {
        BinaryImage image = render_marker(marker, 8, 12);
        int detected = detect_marker(image, dictionary);
        std::printf("marker %d detected as %d\n", marker.id, detected);
    }
    return 0;
}
