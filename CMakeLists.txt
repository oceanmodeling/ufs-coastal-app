# This is the main cmake file for ufs-coastal-app.
cmake_minimum_required(VERSION 3.15)

# Set the project name and version.
project(ufs-coastal-app VERSION 1.0 LANGUAGES C CXX Fortran)

# Required package/s
find_package(MPI REQUIRED COMPONENTS C CXX Fortran)

# Set default bin directory
if(NOT DEFINED CMAKE_INSTALL_BINDIR)
  set(CMAKE_INSTALL_BINDIR bin)
endif()

# Append UFS model modules to find required packages
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/sorc/ufs-weather-model/CMakeModules/Modules)

# Add sub-directory
add_subdirectory(sorc/ufs-weather-model)
