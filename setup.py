import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="camilladsp",
    version="2.0.0",
    author="Henrik Enquist",
    author_email="henrik.enquist@gmail.com",
    description="A library for communicating with CamillaDSP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HEnquist/pycamilladsp",
    packages=setuptools.find_packages(),
    python_requires=">=3",
    install_requires=["PyYAML", "websocket_client"],
)
