from setuptools import setup

with open('requirements.txt') as file:
    install_requires = file.read().splitlines()

setup(
    name='gyraffe',
    description='The (GYRE) acoustic-glitch finder',
    author='Alex Lyttle',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'gyraffe = gyraffe.gyraffe:main',
        ],
    }
)
