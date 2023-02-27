from setuptools import setup, find_packages

setup(
    name='GammaPulsar',
    version='0.0.1',
    packages=find_packages(include=[
        'astropy',
        'gammapy>=1.0',
        'matplotlib>=3.4',
        'scipy<1.10',
        'iminuit>=2.8.0'
        'regions>=0.5',
        'numpy<1.23',
        'pint-pulsar~=0.9.3',
        'fermipy'
    ])
)