import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AGBench", # Replace with your own username
    version="0.0.1",
    author="Gyri Reiersen",
    author_email="gyri.reiersen@tum.de",
    description="A package to benchmark AGB maps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AGBench",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: ETH License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)