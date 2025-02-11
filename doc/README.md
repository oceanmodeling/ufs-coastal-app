## Preparing environment for building documentation

The following commands can be used to create virtual environment using pip and build documentation manually.

```
# Create virtual environment
pip install virtualenv
python -m pip install --upgrade pip
virtualenv build_doc
cd build_doc
source bin/activate
# Install sphinx and dependencies
pip install -r requirements.txt
```

## Building documentation

The documentation can be found under **docs/** directory. To build the documentation, **make html** command needs to be run under this directory. If all the required [Sphinx](https://www.sphinx-doc.org/en/master/) pacages found and installed correctly, the compiled documentation can be found under **build/html/** directory and you could just open **index.html** with browser. Copy this folder to somewhere else outside of the source code to publish it in the next step.

## Publishing documentation

There is no need to publish documentation manually. Once the changes are committed and pushed to the **main** branch, Read the Docs hook will build the documentation and publish it automatically.
