CXX ?= g++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -O2 -Isrc

TEST_BIN := build/tests
SRC := $(wildcard src/*.cpp)
OBJ := $(patsubst src/%.cpp,build/%.o,$(SRC))

all: build/app

build:
	mkdir -p build

build/%.o: src/%.cpp | build
	$(CXX) $(CXXFLAGS) -c $< -o $@

build/app: $(OBJ) | build
	$(CXX) $(CXXFLAGS) $(OBJ) -o $@

test: $(TEST_BIN)
	$(TEST_BIN)

$(TEST_BIN): tests/test_main.cpp $(filter-out build/main.o,$(OBJ)) | build
	$(CXX) $(CXXFLAGS) $^ -o $@

clean:
	rm -rf build

.PHONY: all test clean
