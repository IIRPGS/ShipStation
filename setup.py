from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.readlines()
    requirements = [x.strip() for x in requirements]

setup(
    name="ship_station",
    version="0.1",
    author="Christian",
    author_email="cclark@iirp.edu",
    description="Wrapper for updating/sending Salesforce info to SalesForce",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/IIRPGS/ShipStation/",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
)
