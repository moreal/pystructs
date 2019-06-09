import setuptools
from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    url='https://github.com/moreal/pystructs',
    name='pystructs',
    version='0.1.1',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='c-like struct implementation for human',
    author='moreal',
    author_email='dev.moreal@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ]
)
