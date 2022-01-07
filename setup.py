from ast import literal_eval
from setuptools import setup, find_packages

with open('requirements.txt') as file:
    install_requires = file.read().splitlines()

with open('gyraffe/version.txt') as file:
    version = literal_eval(file.readline())
    
setup(
    name='gyraffe',
    description='The (GYRE) acoustic-glitch finder',
    author='Alex Lyttle',
    version=version,
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'gyraffe = gyraffe.gyraffe:main',
        ],
    },
    package_data={
        '': ['version.txt']
    }
)
