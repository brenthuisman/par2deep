#! /usr/bin/env python
from setuptools import setup

VERSION = '3.3'

with open("README.md", "rb") as f:
    long_descr = f.read()

def main():
    setup(name='par2deep',
          version=VERSION,
          description="Produce, verify and repair par2 files recursively. ",
          long_description=open('README.md').read(),
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Programming Language :: Python :: 3',
              'License :: OSI Approved :: LGPL License',
              'Topic :: Utilities',
              'Operating System :: OS Independent'
          ],
          keywords='par2 file integrity',
          author='Brent Huisman',
          author_email='mail@brenthuisman.net',
          url='https://github.com/brenthuisman/par2deep',
          license='LGPL',
          include_package_data=True,
          zip_safe=False,
          install_requires=['tqdm','configargparse'],
          packages=['par2deep'],
          entry_points={
              "console_scripts": ['par2deep = par2deep:main'],
          },
          )

if __name__ == '__main__':
    main()
