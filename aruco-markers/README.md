# aruco-markers

Detect ArUco-style square markers in a binary image.

> Detect and estimate the pose of fiducial markers with OpenCV ArUco; needs a webcam and printed marker board.

## Overview

An original, self-contained implementation of the **aruco-markers** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic 3x3 marker dictionary with a black border
- Bounding box detection from dark pixels
- Grid sampling with a Hamming distance match
- Rotation-aware comparison against the dictionary

## Stack

`C; POSIX`
The CSV stack is C + POSIX. OpenCV is not installed, so this build implements marker generation and matching over a simple binary image type.

## Run

```bash
make
./build/app
make test
```

## Structure

```text
aruco-markers/
├── src/aruco.cpp          marker dictionary and detection
├── src/aruco.h            image and marker types
├── src/main.cpp           demo program
├── tests/test_main.cpp    unit tests
└── Makefile
```

## Testing

```bash
make test
```

6 tests (`make test`), up from 1: the dictionary, the Hamming distance, the turned cells, the marker in a picture, a turned marker and an empty picture.


## Notes and limitations

- The detector assumes one marker on a plain background, with no perspective.
- There is no camera calibration, pose estimation or sub-pixel refinement.
- Images are synthetic integer arrays rather than camera frames.

## License

BSD-3-Clause. See `LICENSE`.

## About the scope

This is a third-year student project. The build and tests run locally with GCC; there is no portability work beyond the platforms named in the notes.
