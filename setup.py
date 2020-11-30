import os
import subprocess

from distutils.core import Command
from setuptools import setup, find_packages

subprocess.call(
    ('mkdir -p barcoder/data && '
     'git describe --tags --dirty > barcoder/data/ver.tmp '
     '&& mv barcoder/data/ver.tmp barcoder/data/ver '
     '|| rm -f barcoder/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from barcoder import __version__


class CheckVersion(Command):
    description = 'Confirm that the stored package version is correct'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with open('barcoder/data/ver') as f:
            stored_version = f.read().strip()

        git_version = subprocess.check_output(
            ['git', 'describe', '--tags', '--dirty']).strip()

        assert stored_version == git_version
        print('the current version is', stored_version)


package_data = ['data/*']

params = {'author': 'Noah Hoffman',
          'author_email': 'ngh2@uw.edu',
          'description': 'Create specimen label barcodes for Securelink and other applications',
          'name': 'barcoder',
          'packages': find_packages(),
          'package_dir': {'barcoder': 'barcoder'},
          'entry_points': {
              'console_scripts': ['barcoder = barcoder.main:main']
          },
          'version': __version__,
          'package_data': {'barcoder': package_data},
          'test_suite': 'tests',
          'cmdclass': {'check_version': CheckVersion},
          'install_requires': [
              'python-barcode==0.11.0',
              'qrcode==6.1',
              'reportlab==3.5.42',
          ]}

setup(**params)
