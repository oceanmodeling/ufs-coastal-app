## Preparing environment for building documentation

The detailed instructions to install Conda, which is an open-source package management and environment management system, for Linux environment can be found in [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html).

The following commands can be used to create Conda environment and build documentation.

```
# updates conda
conda update -n base -c defaults conda
# creates new environment to build documentation
conda create --name docs
# activates newly created environment for documentation
conda activate docs
# deactivates environment
conda deactivate
# install required modules such as sphinx and bitex extension
conda install sphinx
conda install -c conda-forge sphinxcontrib-bibtex
```

In case of using pip;

```
# install sphinx and related packages
pip install --user sphinx
pip install --user sphinxcontrib-programoutput
pip install --user git+https://github.com/esmci/sphinx_rtd_theme.git@version-dropdown-with-fixes
# add following to .bashrc (in case of installing to your local user)
export PATH=$HOME/.local/bin:$PATH
```

## Building documentation

The documentation can be found under **docs/** directory. To build the documentation, **make html** command needs to be run under this directory. If all the required [Sphinx](https://www.sphinx-doc.org/en/master/) pacages found and installed correctly, the compiled documentation can be found under **build/html/** directory and you could just open **index.html** with browser. Copy this folder to somewhere else outside of the source code to publish it in the next step.

## Publishing documentation

Once the documentation is compiled and **build/** directory is created, it can be used to update the Sphinx document with following commands,

```
# clone documentation branch that stores compiled documentation
git clone --recursive https://github.com/oceanmodeling/ufs-coastal-app.git
cd ufs-coastal-app
git checkout gh-pages
# copy compiled and build/ directory, please rename your build directory as main
cp BUILD_CIRECTORY versions/. 
# Note: in case of having multiple version of the documentation, user needs to edit versions/versions.json and add that version too.
```
