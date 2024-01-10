#!/bin/bash

# usage instructions
usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] ... [TARGETS]

OPTIONS
  -c, --compiler=COMPILER
      compiler and version ("gcc@11.4.0" by default; any available compiler can be given) 
  -i, --install-dir=INSTALL_DIR
      installation prefix ("/opt" for container and "$HOME" for rest by default)
  --install-lmod
      install Lua/Lmod environment module tool to create interface for installed dependencies
  --install-core-pkgs
      install core develelopment packages required for spack-stack installation
  -m, --mpi=MPI
      mpi and version ("openmpi@4.1.5" by default; any available MPI implementation can be given)
  -v, --verbose
      build with verbose output

NOTE: See User's Guide for detailed build instructions for dependencies

EOF_USAGE
}

# print usage error and exit
usage_error () {
  printf "ERROR: $1\n" >&2
  usage >&2
  exit 1
}

# print settings
settings () {
cat << EOF_SETTINGS
Settings:

  COMPILER_TYPE     = ${COMPILER_TYPE}
  COMPILER_VERSION  = ${COMPILER_VERSION}
  INSTALL_DIR       = ${INSTALL_DIR}
  INSTALL_LMOD      = ${INSTALL_LMOD}
  INSTALL_CORE_PKGS = ${INSTALL_CORE_PKGS}
  MPI_TYPE          = ${MPI_TYPE}
  MPI_VERSION       = ${MPI_VERSION}

EOF_SETTINGS
}

# check linux command
check_command () {
  if ! command -v -- "$1" > /dev/null 2>&1; then
    echo "1"
  else
    echo "0"
  fi  
}

# check container or not
check_container () {
  if [ -f /.dockerenv ]; then
    echo "0"
  else
    echo "1"
  fi
}

# check compiler
check_compiler () {
  # check requested MPI available as module
  if [ $(check_command "module") == "0" ]; then
    if [ -z "$(module -t list ${2})" ]; then
      printf "INFO: No loaded module is found for ${2} compiler\n"
      printf "INFO: Checking availablity through spack-stack ...\n"
    fi
  fi
  # check requested compiler through command line
  if [ $(check_command "gcc") == "0" ]; then
    local version=$(gcc --version | head -n 1 | awk -F\) '{print $2}' | tr -d " ")
    if [ "$version" != "${3}" ]; then
      printf "ERROR: Requested ${2} compiler version ${3} is not the same with available one ${version}\n"
      exit
    fi
  fi

  # check compiler is found by spack-stack or not?
  local COMPILER_STRING="${2}@=${3}"
  if [ -z "$(cat ${1}/spack-stack/envs/ufs.local/site/compilers.yaml | grep ${COMPILER_STRING})" ]; then
    printf "ERROR: Requested compiler ${2}@${3} is not found in compilers.yaml! Please select one from the following list. Exiting ...\n"
    spack compiler list
    exit
  fi
}

# check environment variable
check_env_var () {
  if [ x"${1}" == "x" ]; then
    echo "0"
  else
    echo "1"  	
  fi
}

# check mpi
check_mpi () {
  # check requested MPI available as module
  if [ $(check_command "module") == "0" ]; then
    if [ -z "$(module -t list ${2})" ]; then
      printf "INFO: No loaded module is found for ${2} MPI implementation\n"
      printf "INFO: Checking availablity through spack-stack ...\n"
    fi
  fi

  # check requested MPI is available through spack-stack
  if [ -z "$(spack versions --safe ${2} | grep ${3} | tr -d " ")" ]; then
    printf "ERROR: Requested MPI ${2}@${3} is not available through spack-stack! Please select one of the following versions. Exiting ...\n"
    spack versions --safe ${2}
    exit
  else
    printf "INFO: Requested MPI ${2}@${3} is available through spack-stack\n"
  fi
}

# check package manager
check_pkg_manager () {
  if [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    echo $DISTRIB_ID
  fi
}

# install packages with apt package manager
install_with_apt () {
  export DEBIAN_FRONTEND=noninteractive
  apt-get -yqq update
  apt-get -yqq upgrade
  apt install --no-install-recommends -yqq \
  build-essential \
  libkrb5-dev \
  m4 \
  git \
  git-lfs \
  bzip2 \
  unzip \
  tar \
  automake \
  xterm \
  texlive \
  libcurl4-openssl-dev \
  libssl-dev \
  meson \
  mysql-server \
  libmysqlclient-dev  \
  python3-dev  \
  python3-pip \
  wget  \
  rsync \
  tcl  \
  tcl-dev \
  openssh-client
  rm -rf /var/lib/apt/lists/*
}

# process required arguments
if [[ ("$1" == "--help") || ("$1" == "-h") ]]; then
  usage
  exit 0
fi

# check container
IS_CONTAINER=$(check_container)

# default versions
LUA_VERSION=5.1.4.9
LMOD_VERSION=8.7

# default settings
COMPILER="gcc@11.4.0"
if [ ${IS_CONTAINER} == "0" ]; then
  INSTALL_DIR=${INSTALL_DIR:-/opt}
else
  INSTALL_DIR=${INSTALL_DIR:-$HOME}
fi
INSTALL_LMOD=false
INSTALL_CORE_PKGS=false
MPI="openmpi@4.1.5"
VERBOSE=false

# process optional arguments
while :; do
  case $1 in
    --compiler=?*|-c=?*) COMPILER=${1#*=} ;;
    --compiler|--compiler=|-c|-c=) usage_error "$1 requires argument." ;;
    --help|-h) usage; exit 0 ;;
    --install-dir=?*|-i=?*) INSTALL_DIR=${1#*=} ;;
    --install-dir|--install-dir=|-i|-i=) usage_error "$1 requires argument." ;;
    --install-lmod) INSTALL_LMOD=true ;;
    --install-core-pkgs) INSTALL_CORE_PKGS=true ;;
    --mpi=?*|-m=?*) MPI=${1#*=} ;;
    --mpi|--mpi=|-m|-m=) usage_error "$1 requires argument." ;;
    --verbose|-v) VERBOSE=true ;;
    --verbose=?*|--verbose=) usage_error "$1 argument ignored." ;;
    # unknown
    -?*|?*) usage_error "Unknown option $1" ;;
    *) break
  esac
  shift
done

# install code development packages
if [ "${INSTALL_CORE_PKGS}" = true ]; then
  printf "INFO: Installing core packages with OS package manager ...\n"
  case "$(check_pkg_manager)" in
    Ubuntu) install_with_apt ;;
    # unknown
    -?*|?*) printf "ERROR: Unknown OS/package manager! Exiting ... \n" ;;
    *) break
  esac
fi

# install lua/lmod if they are requested
if [ "${INSTALL_LMOD}" = true ]; then
  if [[ $(check_command "wget") == "0" && $(check_command "rsync") == "0" ]]; then
    # create build directory
    if [ ! -d ${INSTALL_DIR}/build ]; then
      mkdir ${INSTALL_DIR}/build
    fi
    cd ${INSTALL_DIR}/build

    # install lua
    if [ ! -d ${INSTALL_DIR}/lua ]; then
      wget -c https://sourceforge.net/projects/lmod/files/lua-${LUA_VERSION}.tar.bz2
      tar -xvf lua-${LUA_VERSION}.tar.bz2
      cd lua-${LUA_VERSION}
      ./configure --prefix=${INSTALL_DIR}/lua
      make
      make install
      cd .. >& /dev/null
    else
      printf "INFO: Lua is already installed! Skip installing Lua ...\n"      
    fi

    # install lmod
    if [ ! -d ${INSTALL_DIR}/lmod ]; then
      wget -c https://sourceforge.net/projects/lmod/files/Lmod-${LMOD_VERSION}.tar.bz2
      tar -xvf Lmod-${LMOD_VERSION}.tar.bz2
      cd Lmod-${LMOD_VERSION}
      ./configure --prefix=${INSTALL_DIR}/lmod --with-lua=${INSTALL_DIR}/lua/bin/lua \
        --with-luac=${INSTALL_DIR}/lua/bin/luac --with-lua_include=${INSTALL_DIR}/lua/include
      make
      make install
      cd .. >& /dev/null
    else
      printf "INFO: Lmod is already installed! Skip installing Lmod ...\n"
    fi

    # activate lmod
    source ${INSTALL_DIR}/lmod/lmod/8.7/init/profile
    if [ $(check_container) == "0" ]; then
      ln -sf ${INSTALL_DIR}/lmod/lmod/8.7/init/profile /etc/profile.d/lmod.sh
    fi
    if [ $(check_command "module") == "1" ]; then
      printf "ERROR: Lmod is not working! Please check the installation ...\n"
      exit
    fi

    # remove build directories
    rm -rf ${INSTALL_DIR}/build
  else
    echo "Please install wget & rsync commands! Exiting ..."
    exit
  fi
fi

# clone spack-stack and activate
cd ${INSTALL_DIR}
if [ ! -d ${INSTALL_DIR}/spack-stack ]; then
  git clone --recurse-submodules https://github.com/jcsda/spack-stack.git
fi
cd spack-stack
export SPACK_ROOT=${INSTALL_DIR}/spack-stack/spack
source setup.sh

# create new environment and activate it
if [ ! -d ${INSTALL_DIR}/spack-stack/envs/ufs.local ]; then
  spack stack create env --site linux.default --template ufs-weather-model --name ufs.local --prefix ${INSTALL_DIR}/ufs.local
fi
cd envs/ufs.local/
spack env activate .

# change directory
cd ${INSTALL_DIR}/spack-stack

# find externals
if [[ ! -f ${INSTALL_DIR}/spack-stack/envs/ufs.local/site/compilers.yaml && \
      ! -f ${INSTALL_DIR}/spack-stack/envs/ufs.local/site/packages.yaml ]]; then
  export SPACK_SYSTEM_CONFIG_PATH="${INSTALL_DIR}/spack-stack/envs/ufs.local/site" && \
  spack external find --scope system --exclude bison --exclude cmake --exclude curl --exclude openssl --exclude openssh
  spack external find --scope system perl
  spack external find --scope system wget
  spack external find --scope system mysql
  spack external find --scope system texlive
  spack compiler find --scope system
  unset SPACK_SYSTEM_CONFIG_PATH
fi

# set compiler and its version
COMPILER_TYPE=$(echo $COMPILER | awk -F\@ '{print $1}')
COMPILER_VERSION=$(echo $COMPILER | awk -F\@ '{print $2}')
check_compiler ${INSTALL_DIR} ${COMPILER_TYPE} ${COMPILER_VERSION}

# set MPI and its version
MPI_TYPE=$(echo $MPI | awk -F\@ '{print $1}')
MPI_VERSION=$(echo $MPI | awk -F\@ '{print $2}')
check_mpi ${INSTALL_DIR} ${MPI_TYPE} ${MPI_VERSION}

# print settings
if [ "${VERBOSE}" = true ] ; then
  settings
fi

# customization of spack-stack configuration
if [ -z "$(cat ${INSTALL_DIR}/spack-stack/envs/ufs.local/spack.yaml | grep ${COMPILER_TYPE}@${COMPILER_VERSION})" ]; then
  spack config add "packages:all:compiler:[${COMPILER_TYPE}@${COMPILER_VERSION}]"
  spack config add "packages:all:providers:mpi:[${MPI_TYPE}@${MPI_VERSION}]"
  spack config add "packages:fontconfig:variants:+pic"
  spack config add "packages:pixman:variants:+pic"
  spack config add "packages:cairo:variants:+pic"
  spack config add "packages:libffi:version:[3.3]"
fi

# concretize
cd ${INSTALL_DIR}/spack-stack/envs/ufs.local
if [[ $(check_env_var __LMOD_REF_COUNT_MODULEPATH) ]]; then
  sed -i 's/tcl/lmod/g' site/modules.yaml
fi
cd /opt/spack-stack
if [ ! -f ${INSTALL_DIR}/spack-stack/envs/ufs.local/spack.lock ]; then
  spack --color always concretize 2>&1 | tee log.concretize
fi

# install dependencies
spack  --color always install --source -j3 2>&1 | tee log.install

# clean
spack gc -y  2>&1 | tee log.clean

# post-installation steps
if [[ $(check_env_var __LMOD_REF_COUNT_MODULEPATH) ]]; then
  spack module lmod refresh -y
else
  spack module tcl refresh -y
fi
spack stack setup-meta-modules
