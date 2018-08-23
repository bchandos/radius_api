import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="radius_api",
    version="0.0.1",
    author="Bill Chandos",
    author_email="chandos@uoregon.edu",
    description="A Radius CRM web services wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU GPLv3 License",
        "Operating System :: OS Independent",
    ),
)