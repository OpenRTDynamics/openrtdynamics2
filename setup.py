import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="openrtdynamics2",
    version="0.2.0",
    author="Christian Klauer",
    author_email="chr@gmail.com",
    description="OpenRTDynamics 2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://openrtdynamics.github.io/",
    packages=setuptools.find_packages(exclude=['tests*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'numpy', 'control', 'colorama', 'prettytable', 'cppyy', 'pygments'
    ],
    python_requires='>=3.6',
)
