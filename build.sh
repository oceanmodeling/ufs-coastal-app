#!/bin/bash

# usage instructions
usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] ... [TARGETS]

OPTIONS
  -a, --app=APPLICATION
      weather model application to build; for example, ATMAQ for Online-CMAQ
      (e.g. CSTLS)
  --bin-dir=BIN_DIR
      installation binary directory name ("bin" by default; any name is available)
  -b, --build-dir=BUILD_DIR
      build directory
  --build-jobs=BUILD_JOBS
      number of build jobs; defaults to 4
  --build-type=BUILD_TYPE
      build type; defaults to RELEASE
      (e.g. DEBUG | RELEASE | RELWITHDEBINFO)
  --clean
      does a "make clean"
  -c, --compiler=COMPILER
      compiler to use; default depends on platform
      (e.g. intel | gnu)
  -h, --help
      show this help guide
  -i, --install-dir=INSTALL_DIR
      installation prefix
  -p, --platform=PLATFORM
      name of machine you are building on
      (e.g. cheyenne | hera | jet | orion | wcoss2)
  --remove
      removes existing build
  -v, --verbose
      build with verbose output

NOTE: See User's Guide for detailed build instructions

EOF_USAGE
}

# print usage error and exit
usage_error () {
  printf "ERROR: $1\n" >&2
  usage >&2
  exit 1
}

# helper to try and load module
function load_module() {
  set +e
  MODF="$1${PLATFORM}.${COMPILER}"
  printf "Loading module ${MODF} ...\n"
  module is-avail ${MODF}
  if [ $? -eq 0 ]; then
    module load ${MODF}
    return
  fi
}

# print settings
settings () {
cat << EOF_SETTINGS
Settings:

  APP=${APPLICATION}
  APP_DIR=${APP_DIR}
  BIN_DIR=${BIN_DIR}
  BUILD_DIR=${BUILD_DIR}
  BUILD_JOBS=${BUILD_JOBS}
  BUILD_TYPE=${BUILD_TYPE}
  CLEAN=${CLEAN}
  COMPILER=${COMPILER}
  INSTALL_DIR=${INSTALL_DIR}
  PLATFORM=${PLATFORM}
  REMOVE=${REMOVE}
  VERBOSE=${VERBOSE}

EOF_SETTINGS
}

# process required arguments
if [[ ("$1" == "--help") || ("$1" == "-h") ]]; then
  usage
  exit 0
fi

# default settings
APP_DIR=$(cd "$(dirname "$(readlink -f -n "${BASH_SOURCE[0]}" )" )" && pwd -P)
BIN_DIR="bin"
BUILD_DIR="${BUILD_DIR:-${APP_DIR}/build}"
BUILD_JOBS=4
BUILD_TYPE="RELEASE"
CLEAN=false
CMAKE_SETTINGS=""
INSTALL_DIR=${INSTALL_DIR:-${APP_DIR}/install}
REMOVE=false
VERBOSE=false

# process optional arguments
while :; do
  case $1 in
    --app=?*|-a=?*) APPLICATION=${1#*=} ;;
    --app|--app=|-a|-a=) usage_error "$1 requires argument." ;;
    --bin-dir=?*) BIN_DIR=${1#*=} ;;
    --bin-dir|--bin-dir=) usage_error "$1 requires argument." ;;
    --build-dir=?*|-b=?*) BUILD_DIR=${1#*=} ;;
    --build-dir|--build-dir=|-b|-b=) usage_error "$1 requires argument." ;;
    --build-type=?*) BUILD_TYPE=${1#*=} ;;
    --build-type|--build-type=) usage_error "$1 requires argument." ;;
    --build-jobs=?*) BUILD_JOBS=$((${1#*=})) ;;
    --build-jobs|--build-jobs=) usage_error "$1 requires argument." ;;
    --clean) CLEAN=true ;;
    --compiler=?*|-c=?*) COMPILER=${1#*=} ;;
    --compiler|--compiler=|-c|-c=) usage_error "$1 requires argument." ;;
    --help|-h) usage; exit 0 ;;
    --install-dir=?*|-i=?*) INSTALL_DIR=${1#*=} ;;
    --install-dir|--install-dir=|-i|-i=) usage_error "$1 requires argument." ;;
    --platform=?*|-p=?*) PLATFORM=${1#*=} ;;
    --platform|--platform=|-p|-p=) usage_error "$1 requires argument." ;;
    --remove) REMOVE=true ;;
    --remove=?*|--remove=) usage_error "$1 argument ignored." ;;
    --verbose|-v) VERBOSE=true ;;
    --verbose=?*|--verbose=) usage_error "$1 argument ignored." ;;
    # unknown
    -?*|?*) usage_error "Unknown option $1" ;;
    *) break
  esac
  shift
done

# ensure uppercase/lowercase
APPLICATION=$(echo ${APPLICATION} | tr '[a-z]' '[A-Z]')
PLATFORM=$(echo ${PLATFORM} | tr '[A-Z]' '[a-z]')
COMPILER=$(echo ${COMPILER} | tr '[A-Z]' '[a-z]')

# check if PLATFORM is set
if [ -z $PLATFORM ] ; then
  printf "\nERROR: Please set PLATFORM.\n\n"
  usage
  exit 0
fi

# set PLATFORM (MACHINE)
MACHINE="${PLATFORM}"

set -eu

# automatically determine compiler
if [ -z "${COMPILER}" ] ; then
  case ${PLATFORM} in
    jet|hera|gaea|gaea-c5) COMPILER=intel ;;
    orion) COMPILER=intel ;;
    wcoss2) COMPILER=intel ;;
    cheyenne) COMPILER=intel ;;
    macos|singularity) COMPILER=gnu ;;
    odin|noaacloud) COMPILER=intel ;;
    *)
      COMPILER=intel
      printf "WARNING: Setting default COMPILER=intel for new platform ${PLATFORM}\n" >&2;
      ;;
  esac
fi

# cmake settings
CMAKE_SETTINGS="\
 -DCMAKE_BUILD_TYPE=${BUILD_TYPE}\
 -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR}\
 -DCMAKE_INSTALL_BINDIR=${BIN_DIR}"

if [ ! -z "${APPLICATION}" ]; then
  CMAKE_SETTINGS="${CMAKE_SETTINGS} -DAPP=${APPLICATION}"

  # application specific cmake settings
  # adcirc
  if [ "${APPLICATION}" == "CSTLA" ]; then
    CMAKE_SETTINGS="${CMAKE_SETTINGS} -DADCIRC_CONFIG=PADCIRC -DBUILD_ADCPREP=ON -DCOUPLED=ON"
  # fvcom
  elif [ "${APPLICATION}" == "CSTLF" ]; then
    CMAKE_SETTINGS="${CMAKE_SETTINGS} -DCOORDINATE_TYPE=SPHERICAL -DWET_DRY=ON"
  # roms
  elif [ "${APPLICATION}" == "CSTLR" ]; then
    CMAKE_SETTINGS="${CMAKE_SETTINGS} -DMY_CPP_FLAGS=BULK_FLUXES" 
  # schism
  elif [ "${APPLICATION}" == "CSTLS" ]; then
    CMAKE_SETTINGS="${CMAKE_SETTINGS} -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON"
  fi
fi

# make settings
MAKE_SETTINGS="-j ${BUILD_JOBS}"
if [ "${VERBOSE}" = true ]; then
  MAKE_SETTINGS="${MAKE_SETTINGS} VERBOSE=1"
fi

# print settings
if [ "${VERBOSE}" = true ] ; then
  settings
fi

# load modules
module purge
module use ${APP_DIR}/sorc/ufs-coastal/modulefiles
load_module "ufs_"
module li

# if build directory already exists then exit
if [ "${REMOVE}" = true ]; then
  # Clean build, install and executable directories
  if [ -d "${BUILD_DIR}" ]; then
    printf "Build directory already exists! Removing ${BUILD_DIR} ...\n"
    rm -rf ${BUILD_DIR}
  fi
  if [ -d "${INSTALL_DIR}" ]; then
    printf "Install directory already exists! Removing ${INSTALL_DIR} ...\n"
    rm -rf ${INSTALL_DIR}
  fi
  # Create new build directory
  mkdir -p ${BUILD_DIR}
  cd ${BUILD_DIR}
else
  # The build directory exists
  if [ -d "${BUILD_DIR}" ]; then
    # Check which application is build
    if [ -f ${BUILD_DIR}/CMakeCache.txt ]; then
      # Query existing app
      APP_BUILD=`cat ${BUILD_DIR}/CMakeCache.txt | grep "APP:BOOL=" | awk -F= '{print $2}'`
      # Check with the requested one
      if [ "${APPLICATION}" != "${APP_BUILD}" ]; then 
        printf "Build directory already exists and used to build -DAPP=${APP_BUILD} but the requested application is -DAPP=${APPLICATION}\n" >&2
        printf "Please clean existing build with --remove option and build again. Exiting ...\n" >&2
        exit
      else
        cd ${BUILD_DIR}
      fi
    fi
  # There is no build directory. Just create it
  else
    mkdir -p ${BUILD_DIR}
    cd ${BUILD_DIR}
  fi
fi

# configure model
printf "Generate CMAKE configuration ...\n" >&2
cmake ${APP_DIR} ${CMAKE_SETTINGS} 2>&1 | tee log.cmake

# build/clean model
if [ "${CLEAN}" = true ]; then
  if [ -f $PWD/Makefile ]; then
    printf "Clean executables ...\n"
    make ${MAKE_SETTINGS} clean 2>&1 | tee log.make
  fi
else
  printf "Build and create executables ...\n"
  make ${MAKE_SETTINGS} install 2>&1 | tee log.make
fi

# move executables
if [ -f "${BUILD_DIR}/sorc/ufs-coastal/ufs_model" ]; then
  printf "Moving executables to final locations ...\n"
  mkdir -p ${INSTALL_DIR}/${BIN_DIR}
  mv ${BUILD_DIR}/sorc/ufs-coastal/ufs_model ${INSTALL_DIR}/${BIN_DIR}/.
fi
