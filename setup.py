from setuptools import setup, find_packages

setup(
    name='ftf-cli',
    version='0.1',
    packages=find_packages(include=['ftf_cli', 'ftf_cli.commands','ftf_cli.commands.templates']),
    include_package_data=True,
    install_requires=[
        'Click',
        'Jinja2',
        'pyyaml',
        'checkov'
    ],
    entry_points='''
        [console_scripts]
        ftf=ftf_cli.cli:cli
    ''',
)