from setuptools import find_packages, setup

setup(
    name="breg-harvester",
    version="0.1.0",
    python_requires=">=3.6",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask>=1.1,<1.2",
        "coloredlogs>=14.0,<15.0",
        "rq>=1.5,<1.6",
        "redis>=3.5,<3.6"
    ],
    extras_require={
        "dev": [
            "autopep8>=1.5,<2.0",
            "pylint>=1.0,<2.0",
            "rope>=0.16.0,<1.0",
            "bumpversion>=0.5.3,<1.0",
            "pytest>=3.10.1,<4.0",
            "mock>=3.0.5,<4.0"
        ]
    },
    entry_points={
        "console_scripts": [
        ]
    }
)
