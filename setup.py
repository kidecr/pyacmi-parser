# setup.py

from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension

extensions = [
    Extension("acmiparse.cutils", ["acmiparse/cutils.pyx"],
              extra_compile_args=[], extra_link_args=[])
]

setup(
    name="acmiparse",
    ext_modules=cythonize(extensions, language_level=3),
    packages=["acmiparse"],
)