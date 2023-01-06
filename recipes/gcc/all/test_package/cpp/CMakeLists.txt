cmake_minimum_required(VERSION 3.15)
project(example_cpp CXX)

add_executable(example_cpp hello.cpp)
add_test(NAME test_cpp COMMAND example_cpp)
