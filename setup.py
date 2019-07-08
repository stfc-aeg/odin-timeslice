"""Setup script for odin_workshop python package."""

import sys
from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='timeslice',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Timeslice ODIN adapter',
      url='https://github.com/stfc-aeg/odin-timeslice',
      author='Cat Carrigan',
      author_email='catherine.carrigan@stfc.ac.uk',
      packages=find_packages(),
      install_requires=required,
      zip_safe=False,
)
