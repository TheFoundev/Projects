#include <cassert>
#include <cstdio>
#include <vector>

#include "../src/aruco.h"

static void test_the_dictionary_is_made() {
    auto dictionary = build_dictionary(5);
    assert(dictionary.size() == 4);
    for (size_t i = 0; i < dictionary.size(); i++) {
        assert(dictionary[i].grid_size == 5);
        for (size_t j = i + 1; j < dictionary.size(); j++) {
            assert(dictionary[i].id != dictionary[j].id);
        }
    }
}

static void test_the_hamming_distance() {
    std::vector<int> left = {1, 0, 1, 1};
    std::vector<int> right = {1, 0, 0, 1};
    assert(hamming_distance(left, left) == 0);
    assert(hamming_distance(left, right) == 1);
}

static void test_the_cells_are_turned() {
    std::vector<int> cells = {0, 1, 1, 0};
    auto turned = rotate_cells(cells, 2);
    assert(turned.size() == cells.size());
    // A quarter turn twice is the other way round.
    auto twice = rotate_cells(turned, 2);
    for (size_t i = 0; i < cells.size(); i++) {
        assert(twice[i] == cells[i]);
    }
}

static void test_the_marker_is_drawn_and_found() {
    auto dictionary = build_dictionary(5);
    const int marker = 2;

    auto picture = render_marker(dictionary[marker], 8, 10);
    assert(detect_marker(picture, dictionary) == marker);
}

static void test_a_turned_marker_is_found() {
    // The detector compares the cells it read with the four turns of every
    // marker of the dictionary, so a marker that is turned is found as well.
    auto dictionary = build_dictionary(5);
    const int marker = 3;

    Marker turned;
    turned.grid_size = dictionary[marker].grid_size;
    turned.cells = rotate_cells(dictionary[marker].cells, turned.grid_size);
    turned.id = -1;

    auto picture = render_marker(turned, 8, 10);
    assert(detect_marker(picture, dictionary) == marker);
}

static void test_an_empty_picture_has_no_marker() {
    auto dictionary = build_dictionary(5);
    BinaryImage empty(40, 40);
    assert(detect_marker(empty, dictionary) == -1);
}

int main() {
    test_the_dictionary_is_made();
    test_the_hamming_distance();
    test_the_cells_are_turned();
    test_the_marker_is_drawn_and_found();
    test_a_turned_marker_is_found();
    test_an_empty_picture_has_no_marker();
    std::printf("all aruco tests passed\n");
    return 0;
}
