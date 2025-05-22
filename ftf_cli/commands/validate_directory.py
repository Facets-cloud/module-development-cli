import click
from subprocess import run, CalledProcessError
from ftf_cli.utils import (
    validate_facets_yaml,
    validate_boolean,
    validate_facets_tf_vars,
)
from checkov.runner_filter import RunnerFilter
from checkov.terraform.runner import Runner


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--check-only",
    is_flag=True,
    default=False,
    help="Check if Terraform files are correctly formatted without modifying them.",
)
@click.option(
    "--skip-terraform-validation",
    default=False,
    callback=validate_boolean,
    help="Skip Terraform validation steps if set to true.",
)
def validate_directory(path, check_only, skip_terraform_validation):
    """Validate the Terraform module and its security aspects."""

    # Check if Terraform is installed
    if run("terraform version", shell=True, capture_output=True).returncode != 0:
        raise click.UsageError(
            "❌ Terraform is not installed. Please install Terraform to continue."
        )

    try:
        # Validate the facets.yaml file in the given path
        validate_facets_yaml(path)
        click.echo("✅ facets.yaml validated successfully.")

        # Run terraform fmt in check mode if check-only flag is present
        fmt_command = (
            ["terraform", "fmt", "-check"] if check_only else ["terraform", "fmt"]
        )
        process = run(
            fmt_command,
            cwd=path,
            shell=False,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in process.stdout.splitlines():
            click.echo(line)
        for line in process.stderr.splitlines():
            click.echo(line)

        validate_facets_tf_vars(path)
        click.echo(
            "✅ Terraform files are correctly formatted."
            if check_only
            else "🎨 Terraform files formatted."
        )

        if not skip_terraform_validation:
            # Run terraform init and validate
            process = run(
                ["terraform", "-chdir={}".format(path), "init", "-backend=false"],
                check=True,
                capture_output=True,
                text=True,
            )

            for line in process.stdout.splitlines():
                click.echo(line)

            for line in process.stderr.splitlines():
                click.echo(line)
            click.echo("🚀 Terraform initialized.")

            process = run(
                ["terraform", "-chdir={}".format(path), "validate"],
                check=True,
                capture_output=True,
                text=True,
            )

            for line in process.stdout.splitlines():
                click.echo(line)

            for line in process.stderr.splitlines():
                click.echo(line)
            click.echo("🔍 Terraform validation successful.")
        else:
            click.echo("⏭ Skipping Terraform validation as per flag.")

        # Run Checkov via API
        runner = Runner()
        report = runner.run(
            root_folder=path, runner_filter=RunnerFilter(framework=["terraform"])
        )

        # Process Checkov results
        if any(
            check
            for check in report.failed_checks
            if check.severity in ["HIGH", "CRITICAL"]
        ):
            click.echo("⛔ Checkov validation failed.")
            for check in report.failed_checks:
                if check.severity in ["HIGH", "CRITICAL"]:
                    click.echo(
                        f"Check: {check.check_id}, Severity: {check.severity}, File: {check.file_path}, Line: {check.file_line}"
                    )
            raise click.UsageError("Checkov validation did not pass.")
        else:
            click.echo("✅ Checkov validation passed.")

    except CalledProcessError as e:
        if e.stdout:
            for line in e.stdout.splitlines():
                click.echo(line)
        if e.stderr:
            for line in e.stderr.splitlines():
                click.echo(line)
        if check_only and "fmt" in str(e):
            raise click.UsageError(
                "❌ Error: Terraform files are not correctly formatted. Please run `terraform fmt` locally to format the files or remove the --check-only flag."
            )
        else:
            raise click.UsageError(f"❌ An error occurred while executing: {e}")
    except Exception as e:
        raise click.UsageError(f"❌ Validation failed: {e}")


if __name__ == "__main__":
    validate_directory()
