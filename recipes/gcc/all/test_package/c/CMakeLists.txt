cmake_minimum_required(VERSION 3.15)
project(example_c C)

add_executable(example_c hello.c)
add_test(NAME test_c COMMAND example_c)
