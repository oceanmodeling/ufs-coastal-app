#!/bin/bash

# usage instructions
usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] ... [TARGETS]

OPTIONS
  -i, --install-dir=INSTALL_DIR
      installation prefix ("/opt" for container and "$HOME" for rest by default)
  --install-lmod
      install Lua/Lmod environment module tool to create interface for installed dependencies
  --install-core-pkgs
      install core develelopment packages required for spack-stack installation
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

  INSTALL_DIR      = ${INSTALL_DIR}
  INSTALL_LMOD     = ${INSTALL_LMOD}
  INSTALL_CORE_PKGS= ${INSTALL_CORE_PKGS}

EOF_SETTINGS
}

# check container or not
check_container () {
  if [ -f /.dockerenv ]; then
    echo "0" 
  else
    echo "1"
  fi
}

# check linux command
check_command () {
  if ! command -v -- "$1" > /dev/null 2>&1; then
    echo "1"
  else
    echo "0"
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
  python3-pip
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
if [ ${IS_CONTAINER} == "0" ]; then
  INSTALL_DIR=${INSTALL_DIR:-/opt}
else
  INSTALL_DIR=${INSTALL_DIR:-$HOME}
fi
INSTALL_LMOD=false
INSTALL_CORE_PKGS=false
VERBOSE=false

# process optional arguments
while :; do
  case $1 in
    --help|-h) usage; exit 0 ;;
    --install-dir=?*|-i=?*) INSTALL_DIR=${1#*=} ;;
    --install-dir|--install-dir=|-i|-i=) usage_error "$1 requires argument." ;;
    --install-lmod) INSTALL_LMOD=true ;;
    --install-core-pkgs) INSTALL_CORE_PKGS=true ;;
    --verbose|-v) VERBOSE=true ;;
    --verbose=?*|--verbose=) usage_error "$1 argument ignored." ;;
    # unknown
    -?*|?*) usage_error "Unknown option $1" ;;
    *) break
  esac
  shift
done

# print settings
if [ "${VERBOSE}" = true ] ; then
  settings
fi

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


