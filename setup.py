from setuptools import setup, find_packages

with open("VERSION", "r") as version_file:
    version = version_file.read().strip()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ftf-cli",
    version=version,
    description="Facets Terraform Cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sanmesh Kakade",
    author_email="sanmesh.kakade@facets.cloud",
    url="https://github.com/Facets-cloud/module-development-cli",
    keywords=["Facets", "CLI", "Terraform"],
    install_requires=[
        "Click",
        "Jinja2",
        "PyYAML",
        "checkov==3.2.414",
        "jsonschema",
        "requests",
        "questionary",
        "facets-hcl",
        "ruamel.yaml",
    ],
    packages=find_packages(
        include=["ftf_cli", "ftf_cli.commands", "ftf_cli.commands.templates"]
    ),
    include_package_data=True,
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "pytest-mock",
            "pyhcl>=0.4.5",
        ],
    },
    entry_points="""
        [console_scripts]
        ftf=ftf_cli.cli:cli
    """,
    python_requires=">=3.10",
)
