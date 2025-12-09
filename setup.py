from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dcmx",
    version="0.1.0",
    author="DCMX Protocol",
    description="Decentralized Mesh Music Network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DCMX-Protocol/DCMX",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.9.0",
        "msgpack>=1.0.7",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dcmx=dcmx.cli:main",
        ],
    },
)
