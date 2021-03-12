from setuptools import setup

__version__ = None
exec(open("or_datasets/_version.py").read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="or-datasets",
    version=__version__,
    author="Flowty",
    author_email="info@flowty.ai",
    url="https://flowty.ai",
    description="OR Datasets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["or_datasets"],
    python_requires=">=3.6",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=[
        "Optimization",
        "Nework Optimization",
        "Combinatorial Optimization",
        "Linear Programming",
        "Integer Programming",
        "Operations Research",
        "Mathematical Programming",
    ],
)
