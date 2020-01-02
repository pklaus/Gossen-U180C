# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    LDESC = open('README.md', 'r').read()
    LDESC = pypandoc.convert(LDESC, 'rst', format='md')
except (ImportError, IOError, RuntimeError) as e:
    print("Could not create long description:")
    print(str(e))
    LDESC = ''

setup(name='u180c',
      version = '0.1dev',
      description = 'Gossen U180C - A Package to query Gossen Metrawatt U180C LAN Gateways',
      long_description = LDESC,
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = 'https://github.com/pklaus/Gossen-U180C',
      license = 'GPL',
      #packages = ['',],
      py_modules = ['u180c',],
      entry_points = {
          'console_scripts': [
              #'u180c = u180c:main',
          ],
      },
      zip_safe = True,
      platforms = 'any',
      install_requires = [
          "pymodbus",
      ],
      keywords = 'Gossen Metrawatt U180C U189A',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Hardware :: Hardware Drivers',
      ]
)
