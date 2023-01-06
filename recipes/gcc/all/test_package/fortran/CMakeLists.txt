cmake_minimum_required(VERSION 3.15)
project(example_fortran Fortran)

add_executable(example_f hello.f90)
add_test(NAME test_fortran COMMAND example_f)
