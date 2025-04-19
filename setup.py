from setuptools import setup, find_packages

setup(
    name="fetchanything",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "tqdm>=4.66.0",
        "argparse>=1.4.0",
        "urllib3>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fetchanything=fetchanything.cli:main",
        ],
    },
    author="Chao-Chung Kuo",
    author_email="chao-chung.kuo@rwth-aachen.de",
    description="A command-line tool to fetch files from websites recursively",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fetchanything",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 