import pytest
from click.testing import CliRunner
from unittest.mock import patch


@pytest.fixture
def runner():
    """Provide a Click CLI test runner that can be used across tests."""
    return CliRunner()


@pytest.fixture
def temp_module_dir(tmp_path):
    """Create a temporary directory for testing module operations."""
    # Create a basic module directory structure
    module_dir = tmp_path / "test-intent" / "test-flavor" / "1.0"
    module_dir.mkdir(parents=True)

    # Create basic files
    facets_yaml = module_dir / "facets.yaml"
    facets_yaml.write_text(
        """
intent: test-intent
flavor: test-flavor
version: 1.0
spec:
  type: object
  properties: {}
outputs:
  default:
    type: "@outputs/test-intent"
    providers: {}
"""
    )

    main_tf = module_dir / "main.tf"
    main_tf.write_text(
        """
# Test main.tf file
resource "aws_s3_bucket" "test_bucket" {
  bucket = "test-bucket"
}
"""
    )

    variables_tf = module_dir / "variables.tf"
    variables_tf.write_text(
        """
# Test variables.tf file
variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-west-2"
}
"""
    )

    outputs_tf = module_dir / "outputs.tf"
    outputs_tf.write_text(
        """
# Test outputs.tf file
output "bucket_id" {
  value       = aws_s3_bucket.test_bucket.id
  description = "The ID of the bucket"
}
"""
    )

    return str(module_dir)


@pytest.fixture
def mock_yaml_validator():
    """Mocks the YAML validator to always pass."""
    with patch("ftf_cli.utils.validate_facets_yaml", return_value=True):
        yield
