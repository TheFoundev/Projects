#include "aruco.h"

#include <algorithm>
#include <cstdlib>

BinaryImage::BinaryImage(int image_width, int image_height)
    : width(image_width), height(image_height), pixels(image_width * image_height, 0) {}

int &BinaryImage::at(int x, int y) { return pixels[y * width + x]; }

int BinaryImage::at(int x, int y) const { return pixels[y * width + x]; }

int Marker::at(int x, int y) const { return cells[y * grid_size + x]; }

int hamming_distance(const std::vector<int> &left, const std::vector<int> &right) {
    int distance = 0;
    for (std::size_t index = 0; index < left.size(); ++index) {
        if (left[index] != right[index]) {
            ++distance;
        }
    }
    return distance;
}

std::vector<int> rotate_cells(const std::vector<int> &cells, int grid_size) {
    std::vector<int> rotated(cells.size(), 0);
    for (int y = 0; y < grid_size; ++y) {
        for (int x = 0; x < grid_size; ++x) {
            rotated[y * grid_size + x] = cells[(grid_size - 1 - x) * grid_size + y];
        }
    }
    return rotated;
}

std::vector<Marker> build_dictionary(int grid_size) {
    std::vector<Marker> dictionary;
    const int patterns[4][9] = {
        {0, 0, 0, 0, 1, 0, 0, 0, 0},
        {1, 0, 0, 0, 1, 0, 0, 0, 1},
        {1, 0, 1, 0, 1, 0, 1, 0, 1},
        {1, 1, 0, 1, 0, 1, 0, 1, 1},
    };
    for (int id = 0; id < 4; ++id) {
        Marker marker;
        marker.grid_size = grid_size;
        marker.id = id;
        marker.cells.assign(grid_size * grid_size, 0);
        for (int y = 0; y < grid_size; ++y) {
            for (int x = 0; x < grid_size; ++x) {
                bool border = x == 0 || y == 0 || x == grid_size - 1 || y == grid_size - 1;
                if (border) {
                    marker.cells[y * grid_size + x] = 1;
                } else if (grid_size == 5) {
                    marker.cells[y * grid_size + x] = patterns[id][(y - 1) * 3 + (x - 1)];
                }
            }
        }
        dictionary.push_back(marker);
    }
    return dictionary;
}

BinaryImage render_marker(const Marker &marker, int cell_pixels, int margin) {
    int size = marker.grid_size * cell_pixels + margin * 2;
    BinaryImage image(size, size);
    for (int y = 0; y < marker.grid_size; ++y) {
        for (int x = 0; x < marker.grid_size; ++x) {
            if (marker.cells[y * marker.grid_size + x] == 0) {
                continue;
            }
            for (int dy = 0; dy < cell_pixels; ++dy) {
                for (int dx = 0; dx < cell_pixels; ++dx) {
                    image.at(margin + x * cell_pixels + dx, margin + y * cell_pixels + dy) = 1;
                }
            }
        }
    }
    return image;
}

struct Box {
    int left;
    int top;
    int right;
    int bottom;
    bool found;
};

static Box find_box(const BinaryImage &image) {
    Box box{0, 0, 0, 0, false};
    for (int y = 0; y < image.height; ++y) {
        for (int x = 0; x < image.width; ++x) {
            if (image.at(x, y) != 1) {
                continue;
            }
            if (!box.found) {
                box = Box{x, y, x, y, true};
            } else {
                box.left = std::min(box.left, x);
                box.top = std::min(box.top, y);
                box.right = std::max(box.right, x);
                box.bottom = std::max(box.bottom, y);
            }
        }
    }
    return box;
}

int detect_marker(const BinaryImage &image, const std::vector<Marker> &dictionary) {
    Box box = find_box(image);
    if (!box.found) {
        return -1;
    }
    int marker_width = box.right - box.left + 1;
    int marker_height = box.bottom - box.top + 1;
    if (marker_width != marker_height || marker_width < 10) {
        return -1;
    }
    for (const Marker &candidate : dictionary) {
        int cell_pixels = marker_width / candidate.grid_size;
        if (cell_pixels < 2) {
            continue;
        }
        std::vector<int> sampled(candidate.grid_size * candidate.grid_size, 0);
        for (int y = 0; y < candidate.grid_size; ++y) {
            for (int x = 0; x < candidate.grid_size; ++x) {
                int center_x = box.left + x * cell_pixels + cell_pixels / 2;
                int center_y = box.top + y * cell_pixels + cell_pixels / 2;
                if (center_x < image.width && center_y < image.height) {
                    sampled[y * candidate.grid_size + x] = image.at(center_x, center_y);
                }
            }
        }
        std::vector<int> current = sampled;
        for (int rotation = 0; rotation < 4; ++rotation) {
            if (hamming_distance(current, candidate.cells) <= 1) {
                return candidate.id;
            }
            current = rotate_cells(current, candidate.grid_size);
        }
    }
    return -1;
}
