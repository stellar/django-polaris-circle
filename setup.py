from setuptools import setup, find_packages


with open("README.rst") as f:
    long_description = f.read()

setup(
    name="django-polaris",
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
    package_dir={"": "polaris_circle"},
    packages=find_packages("polaris_circle"),
    install_requires=["django-polaris~=1.6", "requests>=2.0,<3"],
    python_requires=">=3.7",
)
