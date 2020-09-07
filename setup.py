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
        "coloredlogs>=14.0,<14.1",
        "rq>=1.5,<1.6",
        "redis>=3.5,<3.6",
        "requests>=2.24,<2.25",
        "gevent>=1.4,<1.5",
        "flask-cors>=3.0,<3.1",
        "rdflib>=5.0,<5.1",
        "pyshacl>=0.13,<0.14"
    ],
    extras_require={
        "dev": [
            "autopep8>=1.5,<2.0",
            "pylint>=2.0,<3.0",
            "rope>=0.16.0,<1.0",
            "bumpversion>=0.5.3,<1.0",
            "pytest>=3.10.1,<4.0",
            "mock>=3.0.5,<4.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "harvester=breg_harvester.app:run_wsgi_server"
        ]
    }
)
