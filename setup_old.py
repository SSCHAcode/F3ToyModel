#import setuptools
from __future__ import print_function
from numpy.distutils.core import setup, Extension


f3_lib = Extension(name="fforces.libs",
                   sources = ["src/get_forces_energies.f90",
                              "src/v2_0_harmonic.f90",
                              "src/lattice.f90",
                              "src/get_harmonic_force.f90"],
                   libraries = ["lapack", "blas"])




setup(name = "fforces",
      version = "0.1",
      description = "Python utility to parse a simple toy model calculator for the sscha",
      author = "Lorenzo Monacelli",
      packages = ["fforces"],
      package_dir = {"fforces": "Modules"},
      license = "GPLv3",
      ext_modules = [f3_lib])


def readme():
    with open("README.md") as f:
        return f.read()
