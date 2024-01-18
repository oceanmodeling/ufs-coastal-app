#!/bin/bash

# defs
RED=$(tput bold setaf 1)
BLUE=$(tput bold setaf 4)
NORMAL=$(tput bold sgr0)

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
  -s, --spack-stack-version=SPACK_VERSION
      spack-stack version ("develop" by default; any vaild spack-stack version can be given)
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

  COMPILER_TYPE       = ${COMPILER_TYPE}
  COMPILER_VERSION    = ${COMPILER_VERSION}
  INSTALL_DIR         = ${INSTALL_DIR}
  INSTALL_LMOD        = ${INSTALL_LMOD}
  INSTALL_CORE_PKGS   = ${INSTALL_CORE_PKGS}
  MPI_TYPE            = ${MPI_TYPE}
  MPI_VERSION         = ${MPI_VERSION}
  SPACK_STACK_VERSION = ${SPACK_STACK_VERSION}

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

# check compiler
check_compiler () {
  # check requested MPI available as module
  if [ $(check_command "module") == "0" ]; then
    if [ -z "$(module -t list ${2})" ]; then
      printf "${BLUE}INFO: No loaded module is found for ${2} compiler${NORMAL}\n"
    fi
  fi
  # check requested compiler through command line
  if [ $(check_command "gcc") == "0" ]; then
    local version=$(gcc --version | head -n 1 | awk -F\) '{print $2}' | tr -d " ")
    if [ "$version" != "${3}" ]; then
      printf "${RED}ERROR: Requested ${2} compiler version ${3} is not the same with available one ${version}${NORMAL}\n"
      exit 0
    fi
  fi

  # check compiler is found by spack-stack or not?
  local COMPILER_STRING="${2}@=${3}"
  if [ -f ${1}/spack-stack/envs/ufs.local/site/compilers.yaml ]; then
    if [ -z "$(cat ${1}/spack-stack/envs/ufs.local/site/compilers.yaml | grep ${COMPILER_STRING})" ]; then
      printf "${RED}ERROR:${NORMAL} Requested compiler ${2}@${3} is not found in compilers.yaml! Exiting ...\n"
      if [ $(check_command "spack") == "0" ]; then
        spack compiler list
      fi
      exit 0
    fi
  else
    printf "${RED}ERROR:${NORMAL} ${1}/spack-stack/envs/ufs.local/site/compilers.yaml is not found! Exiting ...\n"
    exit 0
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
  gcc \
  g++ \
  gfortran \
  build-essential \
  libkrb5-dev \
  m4 \
  git \
  git-lfs \
  vim \
  bzip2 \
  unzip \
  tar \
  automake \
  xterm \
  texlive \
  libcurl4-openssl-dev \
  libssl-dev \
  meson \
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

# default versions
LUA_VERSION=5.1.4.9
LMOD_VERSION=8.7

# default settings
COMPILER="gcc@11.4.0"
INSTALL_DIR=${INSTALL_DIR:-$HOME}
INSTALL_LMOD=false
INSTALL_CORE_PKGS=false
MPI="openmpi@4.1.6"
SPACK_STACK_VERSION="develop"
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
    --spack-stack-version=?*|-s=?*) SPACK_STACK_VERSION=${1#*=} ;;
    --spack-stack-version|--spack-stack-version=|-s|-s=) usage_error "$1 requires argument." ;;
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
  printf "${BLUE}INFO: Installing core packages with OS package manager ...${NORMAL}\n"
  case "$(check_pkg_manager)" in
    Ubuntu) install_with_apt ;;
    # unknown
    -?*|?*) printf "${RED}ERROR: Unknown OS/package manager! Exiting ...${NORMAL}\n" ;;
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
    source ${INSTALL_DIR}/lmod/lmod/${LMOD_VERSION}/init/profile
    if [ $(check_container) == "0" ]; then
      ln -sf ${INSTALL_DIR}/lmod/lmod/${LMOD_VERSION}/init/profile /etc/profile.d/lmod.sh
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

  # TODO: add lmod script to /etc/profile.d
  #ln -s ${INSTALL_DIR}/lmod/${LMOD_VERSION}/init/profile /etc/profile.d/lmod.sh

  # TODO: add lmod script to use shell
  #echo "source ${INSTALL_DIR}/lmod/${LMOD_VERSION}/init/profile" >> ${HOME}/.bashrc
fi

# clone spack-stack and activate
cd ${INSTALL_DIR}
if [ ! -d ${INSTALL_DIR}/spack-stack ]; then
  git clone --recurse-submodules https://github.com/jcsda/spack-stack.git
  cd spack-stack
  git checkout ${SPACK_STACK_VERSION}
else
  cd spack-stack
fi
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
  export SPACK_SYSTEM_CONFIG_PATH="${INSTALL_DIR}/spack-stack/envs/ufs.local/site"
  spack external find --scope system --exclude bison --exclude cmake --exclude curl --exclude openssl --exclude openssh
  spack external find --scope system perl
  spack external find --scope system wget
  #spack external find --scope system mysql
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
cd ${INSTALL_DIR}/spack-stack
if [ ! -f ${INSTALL_DIR}/spack-stack/envs/ufs.local/spack.lock ]; then
  spack --color always concretize 2>&1 | tee log.concretize
fi

# install dependencies
spack  --color always install --source -j3 2>&1 | tee log.install

# clean
spack gc -y  2>&1 | tee log.clean

# post-installation steps
spack module tcl refresh -y
spack stack setup-meta-modules
