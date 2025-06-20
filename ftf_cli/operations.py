import os
import json
import zipfile
import tempfile
import base64
from typing import Dict, Optional, Tuple
import requests
import click


class ModuleOperationError(Exception):
    """Custom exception for module operation errors"""

    pass


def cleanup_terraform_files(path: str) -> None:
    """Remove .terraform directories and .terraform.lock.hcl files from the module path"""
    import shutil
    import glob

    # Remove .terraform directories
    terraform_dirs = glob.glob(os.path.join(path, "**/.terraform"), recursive=True)
    for terraform_dir in terraform_dirs:
        if os.path.isdir(terraform_dir):
            shutil.rmtree(terraform_dir)

    # Remove .terraform.lock.hcl files
    lock_files = glob.glob(os.path.join(path, "**/.terraform.lock.hcl"), recursive=True)
    for lock_file in lock_files:
        if os.path.isfile(lock_file):
            os.remove(lock_file)


def create_module_zip(path: str) -> str:
    """Create a zip file of the module directory and return the zip file path"""
    # Clean up terraform files before zipping
    cleanup_terraform_files(path)

    # Create temporary zip file
    temp_fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, path)
                    zipf.write(file_path, arcname)

        return zip_path
    except Exception as e:
        # Clean up on error
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise ModuleOperationError(f"Failed to create zip file: {str(e)}")


def register_module(
        control_plane_url: str,
        username: str,
        token: str,
        path: str,
        git_url: Optional[str] = None,
        git_ref: Optional[str] = None,
        is_feature_branch: bool = False,
        auto_create: bool = False,
        skip_output_write: bool = False,
) -> None:
    """Register a module with the control plane"""

    # Validate inputs
    if not all([control_plane_url, username, token, path]):
        raise ModuleOperationError("Missing required arguments for module registration")

    # Validate path and facets.yaml
    if not os.path.isdir(path):
        raise ModuleOperationError(
            f"Specified path '{path}' does not exist or is not a directory"
        )

    facets_yaml_path = os.path.join(path, "facets.yaml")
    if not os.path.isfile(facets_yaml_path):
        raise ModuleOperationError(
            f"facets.yaml file not found in the specified path '{path}'"
        )

    # Normalize URL
    url = control_plane_url.rstrip("/")
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]

    upload_url = f"https://{url}/cc-ui/v1/modules/upload"

    # Create zip file
    zip_path = None
    try:
        zip_path = create_module_zip(path)

        # Prepare authentication
        auth_string = base64.b64encode(f"{username}:{token}".encode()).decode().strip()
        headers = {"Authorization": f"Basic {auth_string}"}

        # Prepare files for upload and make the request
        with open(zip_path, "rb") as zip_file:
            files = {"file": ("module.zip", zip_file, "application/zip")}

            # Prepare metadata if git info is provided or skip_output_write is set
            if any([git_url, git_ref, is_feature_branch, auto_create, skip_output_write]):
                metadata = {}
                if git_url:
                    metadata["gitUrl"] = git_url
                if git_ref:
                    metadata["gitRef"] = git_ref
                metadata["featureBranch"] = is_feature_branch
                metadata["autoCreate"] = auto_create
                metadata["skipOutputWrite"] = skip_output_write

                metadata_json = json.dumps(metadata).encode()
                temp_metadata_fd, temp_metadata_path = tempfile.mkstemp(suffix=".json")
                with os.fdopen(temp_metadata_fd, "wb") as temp_metadata_file:
                    temp_metadata_file.write(metadata_json)
                try:
                    with open(temp_metadata_path, "rb") as metadata_file:
                        files["metadata"] = (
                            "metadata.json",
                            metadata_file,
                            "application/json",
                        )
                        # Make the request
                        response = requests.post(upload_url, headers=headers, files=files)
                finally:
                    os.remove(temp_metadata_path)
            else:
                # Make the request
                response = requests.post(upload_url, headers=headers, files=files)

        # Check response
        if response.status_code == 200:
            click.echo("Module registered successfully.")
        elif 400 <= response.status_code < 600:
            try:
                error_message = response.json().get(
                    "message",
                    f"Operation failed with status code {response.status_code}",
                )
            except (ValueError, AttributeError):
                error_message = (
                    f"Operation failed with status code {response.status_code}"
                )
            raise ModuleOperationError(
                f"❌ Error: {error_message} (HTTP {response.status_code})"
            )
        else:
            raise ModuleOperationError(
                f"❌ Error: Operation failed with unexpected status code {response.status_code}"
            )

    finally:
        # Clean up zip file
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)


def publish_module(
        control_plane_url: str,
        username: str,
        token: str,
        intent: str,
        flavor: str,
        version: str,
) -> None:
    """Publish a module to make it available for production use"""

    # Validate inputs
    if not all([control_plane_url, username, token, intent, flavor, version]):
        raise ModuleOperationError("Missing required arguments for module publishing")

    # Normalize URL
    url = control_plane_url.rstrip("/")
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]

    publish_url = f"https://{url}/cc-ui/v1/modules/intent/{intent}/flavor/{flavor}/version/{version}/mark-published"

    # Prepare authentication
    auth_string = base64.b64encode(f"{username}:{token}".encode()).decode().strip()
    headers = {"Authorization": f"Basic {auth_string}"}

    # Make the request
    response = requests.post(publish_url, headers=headers)

    # Check response
    if response.status_code == 200:
        click.echo("Module marked as published successfully.")
    elif 400 <= response.status_code < 600:
        try:
            error_message = response.json().get(
                "message", f"Operation failed with status code {response.status_code}"
            )
        except (ValueError, AttributeError):
            error_message = f"Operation failed with status code {response.status_code}"
        raise ModuleOperationError(
            f"❌ Error: {error_message} (HTTP {response.status_code})"
        )
    else:
        raise ModuleOperationError(
            f"❌ Error: Operation failed with unexpected status code {response.status_code}"
        )
