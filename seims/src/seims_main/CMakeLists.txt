# CMake build for Windows, Linux, and macOS
# Author         : LiangJun Zhu, JunZhi Liu
# Contact        : zlj@lreis.ac.cn
# Latest updated : Mar. 31, 2017
#

cmake_minimum_required(VERSION 3.1)
IF (COMMAND CMAKE_POLICY)
    CMAKE_POLICY(SET CMP0015 NEW)
    SET(CMAKE_MACOSX_RPATH 1)
ENDIF (COMMAND CMAKE_POLICY)

################# SEIMS Version ##################
SET(SEIMSPRJ "seims")
IF (STORM EQUAL 1)
    SET(SEIMSPRJ ${SEIMSPRJ}_storm)
    MESSAGE(STATUS "Storm mode...")
    ADD_DEFINITIONS(-DSTORM_MODE)
ELSE ()
    SET(SEIMSPRJ ${SEIMSPRJ}_longterm)
    MESSAGE(STATUS "Longterm mode...")
ENDIF ()
IF (PARALLEL STREQUAL MPI)
    SET(SEIMSPRJ ${SEIMSPRJ}_mpi)
    MESSAGE(STATUS "MPI&OpenMP version...")
    ADD_DEFINITIONS(-DMONGO_HAVE_STDINT -DUSE_MONGODB -DMODULE_EXPORTS)
ELSE ()
    SET(SEIMSPRJ ${SEIMSPRJ}_omp)
    MESSAGE(STATUS "OpenMP version...")
    ADD_DEFINITIONS(-DMONGO_HAVE_STDINT -DUSE_MONGODB -DMODULE_EXPORTS -DMULTIPLY_REACHES)
ENDIF ()
IF (ARCH EQUAL 64)
    SET(SEIMSPRJ ${SEIMSPRJ}_x64)
    MESSAGE(STATUS "64-bit version...")
ELSE ()
    SET(SEIMSPRJ ${SEIMSPRJ}_x32)
    MESSAGE(STATUS "32-bit version...")
ENDIF ()
SET(SEIMSPRJ ${SEIMSPRJ}_prj)
PROJECT(${SEIMSPRJ})
################# OS platform   ##################
if (WIN32)
    add_definitions(-Dwindows)
    if (MSVC)
        add_definitions(-DMSVC)
    endif ()
elseif (APPLE)
    add_definitions(-Dmacos)
else ()
    add_definitions(-Dlinux)
endif ()
if (NOT MSVC)
    SET (CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g")
    SET (CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -fPIC -g -ggdb")
    SET (CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O2 -Wall -fPIC")
endif ()
# Set a default build type for single-configuration
# CMake generators if no build type is set.
IF(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
   SET(CMAKE_BUILD_TYPE RelWithDebInfo)
ENDIF()
# Set runtime library type
include(SetThreadFlagMSVC)
################# Find packages ##################
# GDAL, Bson, Mongoc, MPI, and OpenMP are required
IF (WIN32)
    # 1. GDAL
    SET(GDAL_DIR $ENV{GDAL_DIR})
    SET(GDAL_DIR $ENV{GDAL_DIR})
    SET(GDAL_INCLUDE_DIR ${GDAL_DIR}\\include)
    SET(GDAL_LIBRARIES ${GDAL_DIR}\\lib)
    SET(GDAL_BIN_DIR ${GDAL_DIR}\\bin)
    SET(GDAL_LIBRARY ${GDAL_LIBRARIES}\\gdal_i.lib)
    # 2. Bson and MongoC
    include(FindBson)
    include(FindMongoC)
    IF (PARALLEL STREQUAL MPI)
        # 3. MPI
        IF (ARCH EQUAL 64)
            SET(MPI_LIB $ENV{MSMPI_LIB64})
        ELSE ()
            SET(MPI_LIB $ENV{MSMPI_LIB32})
        ENDIF ()
        SET(MPI_HOME $ENV{MSMPI_BIN})
        SET(MPI_INCLUDE_PATH $ENV{MSMPI_INC})
        SET(MPI_LIBRARIES ${MPI_LIB}\\msmpi.lib)
    ENDIF ()
ELSE ()
    # 1. GDAL CMake will find GDAL and get GDAL_INCLUDE_DIR and GDAL_LIBRARY.
    find_package(GDAL REQUIRED)
    # 2. Bson and MongoC
    include(FindBson)
    include(FindMongoC)
    IF (PARVERSION STREQUAL MPI)
        # 3. MPI
        find_package(MPI REQUIRED)
        set(CMAKE_CXX_FLAG "${CMAKE_CXX_FLAG} ${MPI_COMPILE_FLAGS}")
        set(CMAKE_CXX_LINK_FLAGS "${CMAKE_CXX_LINK_FLAGS} ${MPI_LINK_FLAGS}")
    ENDIF ()
ENDIF ()
IF (GDAL_LIBRARY)
    MESSAGE(STATUS "FOUND GDAL: ${GDAL_LIBRARY}")
ENDIF ()
IF (BSON_LIBRARIES)
    MESSAGE(STATUS "FOUND BSON: ${BSON_LIBRARIES}")
ENDIF ()
IF (MONGOC_LIBRARIES)
    MESSAGE(STATUS "FOUND MongoC: ${MONGOC_LIBRARIES}")
ENDIF ()
IF (MPI_LIBRARIES)
    MESSAGE(STATUS "FOUND MPI: ${MPI_LIBRARIES}")
ENDIF ()
# 4. Add support for OpenMP
FIND_PACKAGE(OpenMP)
IF (OPENMP_FOUND)
    add_definitions(-DSUPPORT_OMP)
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
ENDIF ()
### Active C++11 standard, cross-platform. This requires CMake 3.1+
# SET(CMAKE_CXX_STANDARD 11) CMake may make mistake in intel c/c++ compiler
# 12.1, so make some test when setting the C++ Standard.
# refers to https://github.com/biicode/client/issues/10
include(CheckCXXCompilerFlag)
set(ENABLE_CXXFLAGS_TO_CHECK
    -std=gnu++11
    -std=c++11
    -std=gnu++0x
    -std=c++0x)
MESSAGE(STATUS "CHECK CXX STANDARD FLAGS...")
foreach(flag ${ENABLE_CXXFLAGS_TO_CHECK})
    string(REPLACE "-std=" "_" flag_var ${flag})
    string(REPLACE "+" "x" flag_var ${flag_var})
    check_cxx_compiler_flag("${flag}" COMPILER_HAS_CXX_FLAG${flag_var})
    if(COMPILER_HAS_CXX_FLAG${flag_var})
        MESSAGE(STATUS "${flag}...yes")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${flag}")
        break()
    endif()
endforeach()
MESSAGE(STATUS "USED CXX FLAGS: ${CMAKE_CXX_FLAGS}")
################# Install directory ##################
IF (INSTALL_PREFIX)
    SET(CMAKE_INSTALL_PREFIX ${INSTALL_PREFIX})
    SET(INSTALL_DIR ${INSTALL_PREFIX})
ELSE ()
    SET(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR})
    SET(INSTALL_DIR ${CMAKE_SOURCE_DIR}/bin)
ENDIF ()
##############  Set common libraries   ###############
set(UTILS_INC ${CMAKE_CURRENT_SOURCE_DIR}/../commonlibs/UtilsClass)
set(UTILS_FILES ${UTILS_INC}/utils.cpp ${UTILS_INC}/ModelException.cpp)
set(MONGO_INC ${CMAKE_CURRENT_SOURCE_DIR}/../commonlibs/MongoUtilClass)
set(MONGO_FILES ${MONGO_INC}/MongoUtil.cpp)
SET(RASTER_INC ${CMAKE_CURRENT_SOURCE_DIR}/../commonlibs/RasterClass)
SET(RASTER_FILES ${RASTER_INC}/clsRasterData.cpp)
########  Stand-alone libraries/programs   ###########
SET(BASE_HOME ${CMAKE_CURRENT_SOURCE_DIR}/base)
SET(BASE_INC ${BASE_HOME}/util ${BASE_HOME}/data ${BASE_HOME}/module_setting ${BASE_HOME}/bmps)
SET(MODULE_HOME ${CMAKE_CURRENT_SOURCE_DIR}/modules)
SET(MAIN_HOME ${CMAKE_CURRENT_SOURCE_DIR}/main)
############  Set include directories    #############
SET(MODULE_SRC ${CMAKE_CURRENT_SOURCE_DIR}/base/util/SimulationModule.cpp)
INCLUDE_DIRECTORIES(${GDAL_INCLUDE_DIR} ${BSON_INCLUDE_DIR} ${MONGOC_INCLUDE_DIR} ${UTILS_INC} ${MONGO_INC} ${RASTER_INC} ${BASE_INC})
IF (PARALLEL STREQUAL MPI)
    INCLUDE_DIRECTORIES(${CMAKE_CURRENT_SOURCE_DIR}/main/main_omp ${MPI_INCLUDE_PATH})
    LINK_LIBRARIES(${MPI_LIBRARIES})
ENDIF ()
IF (MSVC)
    SET_PROPERTY(GLOBAL PROPERTY USE_FOLDERS ON)
ENDIF ()
############  step into subdirectories   #############
ADD_SUBDIRECTORY(${BASE_HOME})
ADD_SUBDIRECTORY(${MODULE_HOME})
ADD_SUBDIRECTORY(${MAIN_HOME})
### For CLion to implement the "make install" command
add_custom_target(install_${PROJECT_NAME}
        $(MAKE) install
        DEPENDS ${PROJECT_NAME}
        COMMENT "Installing ${PROJECT_NAME}")
IF (PARALLEL STREQUAL MPI)
    MESSAGE(STATUS "    Compiling SEIMS_MPI done")
ELSE ()
    MESSAGE(STATUS "    Compiling SEIMS_OMP done")
ENDIF ()
