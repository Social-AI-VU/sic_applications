from setuptools import setup
import six

requirements = ['numpy', 'redis', 'Pillow', 'six',]

if six.PY3:
    # cannot be installed on nao
    requirements += ["paramiko", ]

setup(
    name='sic_framework',
    version='0.0.1',
    author='Koen Hindriks',
    author_email='k.v.hindriks@vu.nl',
    packages=['sic_framework'],
    install_requires=requirements,
)
