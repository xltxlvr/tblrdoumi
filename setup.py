from setuptools import setup, find_packages

setup(
    name="tblrDoumi",
    version="3.9",
    packages=find_packages(),
    install_requires=[
        PySide6,
        openpyxl,
    ],
    entry_points={
        "console_scripts": [
            "tblrDoumi-run=tblrDoumi.main:main",  
        ],
    },
    python_requires=">=3.9",
)