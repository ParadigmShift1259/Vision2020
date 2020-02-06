import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Paradigm Shift Team 1259",
    version="0.0.1",
    author="Team1259",
    author_email="1259paradigmshift@gmail.com",
    description="Paradigm Shift Team 1259 Infinite Recharge Vision 2020",
    long_description=This project provides the vision capabilties required for Infinite Recharge games 2020,
    long_description_content_type="text/markdown",
    url="https://github.com/ParadigmShift1259/Vision2020",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
