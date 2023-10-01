cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(mlpack CONFIG REQUIRED)
find_package(HDF5 CONFIG REQUIRED)

add_executable(example src/example.cpp)
target_link_libraries(example mlpack::mlpack HDF5::HDF5)
