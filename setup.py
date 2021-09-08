from setuptools import setup, find_packages


with open("README.rst") as f:
    long_description = f.read()

setup(
    dependency_links=[
        "git+https://github.com/stellar/django-polaris.git@custodial-support#egg=django-polaris"
    ],
    name="django-polaris-circle",
    version="0.1.0",
    description="A circle-based custody implementation for django-polaris",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Jake Urban",
    author_email="jake@stellar.org",
    license="Apache license 2.0",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    keywords=["stellar", "sdf", "anchor", "polaris", "circle", "usdc", "custody"],
    include_package_data=True,
    packages=find_packages(),
    install_requires=["requests>=2.0,<3"],
    python_requires=">=3.7",
)
