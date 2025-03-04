import os
import click
from subprocess import run, CalledProcessError
from ftf_cli.utils import validate_facets_yaml
from checkov.runner_filter import RunnerFilter
from checkov.terraform.runner import Runner


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--check-only', is_flag=True, help='Check if Terraform files are correctly formatted without modifying them.')
def validate_directory(path, check_only):
    """Validate the Terraform module and its security aspects."""
    try:
        # Validate the facets.yaml file in the given path
        validate_facets_yaml(path)
        click.echo("✅ facets.yaml validated successfully.")

        # Run terraform fmt in check mode if check-only flag is present
        fmt_command = ["terraform", "fmt", "-check"] if check_only else ["terraform", "fmt"]
        run(fmt_command, cwd=path, check=True)
        click.echo("✅ Terraform files are correctly formatted." if check_only else "🎨 Terraform files formatted.")

        # Run terraform init and validate
        run(["terraform", "-chdir={}".format(path), "init", "-backend=false"], check=True)
        click.echo("🚀 Terraform initialized.")

        run(["terraform", "-chdir={}".format(path), "validate"], check=True)
        click.echo("🔍 Terraform validation successful.")

        # Run Checkov via API
        runner = Runner()
        report = runner.run(root_folder=path, runner_filter=RunnerFilter(framework=['terraform']))

        # Process Checkov results
        if any(check for check in report.failed_checks if check.severity in ['HIGH', 'CRITICAL']):
            click.echo("⛔ Checkov validation failed.")
            for check in report.failed_checks:
                if check.severity in ['HIGH', 'CRITICAL']:
                    click.echo(f"Check: {check.check_id}, Severity: {check.severity}, File: {check.file_path}, Line: {check.file_line}")
            raise Exception("Checkov validation did not pass.")
        else:
            click.echo("✅ Checkov validation passed.")

    except CalledProcessError as e:
        if check_only and "fmt" in str(e):
            click.echo("❌ Error: Terraform files are not correctly formatted. Please run `terraform fmt` locally to format the files.")
        else:
            click.echo(f"❌ An error occurred while executing: {e}")
        raise e
    except click.UsageError as ue:
        click.echo(ue.message)
        raise ue
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise e


if __name__ == "__main__":
    validate_directory()
