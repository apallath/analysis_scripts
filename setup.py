import os
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy
try:
    numpy_include = numpy.get_include()
except AttributeError:
    numpy_include = numpy.get_numpy_include()


# scan the 'INDUSAnalysis' directory for extension files
def scandir(dir, files=[]):
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        if os.path.isfile(path) and path.endswith(".pyx"):
            files.append(path.replace(os.path.sep, ".")[:-4])
        elif os.path.isdir(path):
            scandir(path, files)
    return files


# generate an Extension object from its dotted name
def makeExtension(extName):
    extPath = extName.replace(".", os.path.sep) + ".pyx"
    return Extension(
        extName,
        [extPath],
        include_dirs=[numpy_include],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=["-O3", "-Wall"],
        extra_link_args=['-g'],
    )


# get the list of extensions
extNames = scandir("INDUSAnalysis")

# and build up the set of Extension objects
extensions = [makeExtension(name) for name in extNames]

# finally, we can pass all this to distutils
setup(
    name="INDUSAnalysis",
    version='0.2a0',
    packages=["INDUSAnalysis",
              "INDUSAnalysis.lib",
              "INDUSAnalysis.ensemble",
              "INDUSAnalysis.ensemble.proteins",
              "INDUSAnalysis.ensemble.proteins.dewetting",
              "INDUSAnalysis.ensemble.proteins.denaturation",
              "INDUSAnalysis.ensemble.polymers"],
    ext_modules=extensions,
    cmdclass={'build_ext': build_ext},
)
