import os
import click
from subprocess import run, CalledProcessError
from ftf_cli.utils import validate_facets_yaml
from checkov.runner_filter import RunnerFilter
from checkov.terraform.runner import Runner


@click.command()
@click.option('-p', '--path', default='.', help='Path to the module directory containing facets.yaml')
def validate_directory(path):
    """Validate the Terraform module and its security aspects."""
    try:
        # Validate the facets.yaml file in the given path
        validate_facets_yaml(path)
        click.echo("facets.yaml validated successfully.")

        # Run terraform fmt
        run(["terraform", "fmt"], cwd=path, check=True)
        click.echo("Terraform files formatted.")

        # Run terraform init and validate
        run(["terraform", "-chdir={}".format(path), "init", "-backend=false"], check=True)
        click.echo("Terraform initialized.")

        run(["terraform", "-chdir={}".format(path), "validate"], check=True)
        click.echo("Terraform validation successful.")

        # Run Checkov via API
        runner = Runner()
        report = runner.run(root_folder=path, runner_filter=RunnerFilter(framework=['terraform']))

        # Process Checkov results
        if any(check for check in report.failed_checks if check.severity in ['HIGH', 'CRITICAL']):
            click.echo("Checkov validation failed.")
            for check in report.failed_checks:
                if check.severity in ['HIGH', 'CRITICAL']:
                    click.echo(f"Check: {check.check_id}, Severity: {check.severity}, File: {check.file_path}, Line: {check.file_line}")
            raise Exception("Checkov validation did not pass.")
        else:
            click.echo("Checkov validation passed.")

    except CalledProcessError as e:
        click.echo(f"An error occurred while executing: {e}")
    except click.UsageError as ue:
        click.echo(ue.message)
    except Exception as e:
        click.echo(f"Validation failed: {e}")


if __name__ == "__main__":
    validate_directory()
