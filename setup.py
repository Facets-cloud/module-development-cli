from setuptools import setup, find_packages

setup(
    name='ftf-cli',
    version='0.1',
    packages=find_packages(include=['ftf_cli', 'ftf_cli.commands','ftf_cli.commands.templates']),
    include_package_data=True,
    install_requires=[
        'Click',
        'Jinja2',
        'PyYAML',
        'checkov',
        'jsonschema',
        'requests',
        'questionary',
        'python-hcl2 @ git+https://github.com/Facets-cloud/python-hcl2.git@main',
        'ruamel.yaml',
        'hcl',
        'lark',
    ],
    extras_require={
        'dev': [
            'pytest>=8.3.5',
            'pytest-mock',
            'pyhcl>=0.4.5',
        ],
    },
    entry_points='''
        [console_scripts]
        ftf=ftf_cli.cli:cli
    ''',
    python_requires='>=3.9',
)