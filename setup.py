from setuptools import setup, find_packages

setup(
    name='chkm0SVE',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Pillow',
        'tqdm',
    ],
    entry_points={
        'console_scripts': [
            'chkm0SVE = chkm0SVE:main',
        ],
    },
)
