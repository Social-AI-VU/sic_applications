from setuptools import setup, find_packages

# Basic (bare minimum) requirements for local machine
local_requirements = [
    'opencv-python',
    'paramiko',
    'pyaudio',
    'pyspacemouse',
    'scp',
]

# Dependencies specific to each component or server
extras_require = {
    'dialogflow': [
        'google-cloud-dialogflow',
    ],
    'face_detection_dnn': [
        'matplotlib',
        'pandas',
        'pyyaml',
        'torch',
        'torchvision',
        'tqdm',
    ],
    'local': local_requirements,
}

# Common requirements for both local machine and robot
common_requirements = [
    'numpy',
    'Pillow',
    'redis',
    'six',
]

setup(
    name='social-interaction-cloud',
    version='2.0.3',
    author='Koen Hindriks',
    author_email='k.v.hindriks@vu.nl',
    packages=find_packages(),
    install_requires=common_requirements,
    extras_require=extras_require,
)
