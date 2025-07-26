# from setuptools import setup
#
# setup()

from setuptools import setup, find_packages

setup(
    name="diploma-frontend",
    version="0.7",
    description="Frontend for diploma project",
    long_description="Frontend for diploma project",
    author="Skillbox",
    license="BSD-3-Clause",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 5",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    packages=find_packages(),  # автоматически найдет все пакеты (включая `diploma_frontend`)
    package_data={
        "diploma_frontend": [
            "static/**/*",
            "templates/**/*",
        ],
    },
)
