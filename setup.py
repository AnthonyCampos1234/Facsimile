from setuptools import setup, find_packages

with open("requirements/requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="facsimile",
    version="0.1",
    packages=find_packages(),
    install_requires=required
) 