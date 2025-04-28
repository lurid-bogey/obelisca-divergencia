import setuptools
from setuptools import setup, find_packages

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="obeliscaDivergencia",
    version="0.7.0",
    author="lurid-bogey",
    author_email="lurid-bogey@gmx.com",
    description="Obelisca Divergencia is a helpful Azure OpenAI client.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lurid-bogey/obelisca-divergencia",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "obeliscaDivergencia": ["assets/", "gui/", "utils/", "tests/"],
    },
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "obeliscaDivergencia = obeliscaDivergencia.main:main",
        ],
    },
    scripts=[
        "obeliscaDivergencia/build/build.bat",
    ],
    license="GNU General Public License v3.0",
    keywords=["Azure", "OpenAI", "Client", "Chat", "GUI"],
)
