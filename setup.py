from setuptools import setup


setup(
  name='sic_framework',
  version='0.0.1',
  author='Koen Hindriks',
  author_email='k.v.hindriks@vu.nl',
  packages=['sic_framework'],
  install_requires=['numpy', 'redis', 'Pillow', 'six', "paramiko"],
)
