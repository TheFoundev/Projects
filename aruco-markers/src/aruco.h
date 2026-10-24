#ifndef ARUCO_H
#define ARUCO_H

#include <vector>

struct BinaryImage {
    int width;
    int height;
    std::vector<int> pixels;

    BinaryImage(int image_width, int image_height);
    int &at(int x, int y);
    int at(int x, int y) const;
};

// Marker is a square grid where 1 means dark and 0 means light. The outer
// one-cell border is always dark and the inner cells carry the id.
struct Marker {
    int grid_size;
    std::vector<int> cells;
    int id;

    int at(int x, int y) const;
};

std::vector<Marker> build_dictionary(int grid_size);
BinaryImage render_marker(const Marker &marker, int cell_pixels, int margin);
int detect_marker(const BinaryImage &image, const std::vector<Marker> &dictionary);
int hamming_distance(const std::vector<int> &left, const std::vector<int> &right);
std::vector<int> rotate_cells(const std::vector<int> &cells, int grid_size);

#endif
