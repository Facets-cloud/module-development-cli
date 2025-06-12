import pytest
import tempfile
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from ftf_cli.commands.validate_directory import validate_directory


class TestValidateDirectoryProviderValidation:
    """Test provider validation integration in validate_directory command."""

    def test_validate_directory_with_provider_blocks_fails(self):
        """Test that validate_directory fails when provider blocks are present."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a module with provider block
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "test" {
  ami = "ami-123"
}
''')
            
            variables_tf = os.path.join(temp_dir, "variables.tf")
            with open(variables_tf, "w") as f:
                f.write('''
variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Instance name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "inputs" {
  description = "Inputs"
  type        = object({})
}
''')
            
            facets_yaml = os.path.join(temp_dir, "facets.yaml")
            with open(facets_yaml, "w") as f:
                f.write('''
intent: test-intent
flavor: test-flavor
version: "1.0"
description: Test module for provider validation
clouds:
  - aws
spec:
  type: object
  properties: {}
''')
            
            # Mock external dependencies to focus on provider validation
            with patch('ftf_cli.commands.validate_directory.run') as mock_run:
                # Mock terraform version check to succeed
                mock_run.return_value.returncode = 0
                
                # Mock the other validation steps to pass
                with patch('ftf_cli.utils.validate_facets_yaml') as mock_validate_yaml, \
                     patch('ftf_cli.utils.validate_facets_tf_vars') as mock_validate_vars:
                    
                    mock_validate_yaml.return_value = True
                    mock_validate_vars.return_value = True
                    
                    # Run the command
                    result = runner.invoke(validate_directory, [temp_dir, '--skip-terraform-validation', 'true'])
                    
                    # Should fail due to provider blocks
                    assert result.exit_code != 0
                    assert "Provider blocks are not allowed in module files" in result.output
                    assert "main.tf" in result.output

    def test_validate_directory_without_provider_blocks_continues(self):
        """Test that validate_directory continues when no provider blocks are present."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a module without provider blocks
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            variables_tf = os.path.join(temp_dir, "variables.tf")
            with open(variables_tf, "w") as f:
                f.write('''
variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Instance name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "inputs" {
  description = "Inputs"
  type        = object({})
}
''')
            
            facets_yaml = os.path.join(temp_dir, "facets.yaml")
            with open(facets_yaml, "w") as f:
                f.write('''
intent: test-intent
flavor: test-flavor
version: "1.0"
description: Test module for provider validation
clouds:
  - aws
spec:
  type: object
  properties: {}
''')
            
            # Mock external dependencies
            with patch('ftf_cli.commands.validate_directory.run') as mock_run:
                # Mock terraform version check to succeed
                mock_run.return_value.returncode = 0
                
                # Mock the checkov validation to pass
                with patch('ftf_cli.utils.validate_facets_yaml') as mock_validate_yaml, \
                     patch('ftf_cli.utils.validate_facets_tf_vars') as mock_validate_vars, \
                     patch('checkov.terraform.runner.Runner') as mock_runner_class:
                    
                    mock_validate_yaml.return_value = True
                    mock_validate_vars.return_value = True
                    
                    # Mock Checkov runner
                    mock_runner = MagicMock()
                    mock_runner_class.return_value = mock_runner
                    mock_report = MagicMock()
                    mock_report.failed_checks = []  # No failed checks
                    mock_runner.run.return_value = mock_report
                    
                    # Run the command
                    result = runner.invoke(validate_directory, [temp_dir, '--skip-terraform-validation', 'true'])
                    
                    # Should pass provider validation and continue
                    assert "No provider blocks found in Terraform files" in result.output
                    # Should not fail due to provider validation
                    assert "Provider blocks are not allowed" not in result.output


    def test_validate_directory_detects_nested_provider_blocks(self):
        """Test that validate_directory detects provider blocks in nested directories."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main module without provider blocks
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Create nested directory with provider block
            nested_dir = os.path.join(temp_dir, "modules", "vpc")
            os.makedirs(nested_dir)
            nested_tf = os.path.join(nested_dir, "vpc.tf")
            with open(nested_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-east-1"
  alias  = "east"
}

resource "aws_vpc" "nested" {
  cidr_block = "10.0.0.0/16"
}
''')
            
            variables_tf = os.path.join(temp_dir, "variables.tf")
            with open(variables_tf, "w") as f:
                f.write('''
variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Instance name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "inputs" {
  description = "Inputs"
  type        = object({})
}
''')
            
            facets_yaml = os.path.join(temp_dir, "facets.yaml")
            with open(facets_yaml, "w") as f:
                f.write('''
intent: test-intent
flavor: test-flavor
version: "1.0"
description: Test module for provider validation
clouds:
  - aws
spec:
  type: object
  properties: {}
''')
            
            # Mock external dependencies to focus on provider validation
            with patch('ftf_cli.commands.validate_directory.run') as mock_run:
                # Mock terraform version check to succeed
                mock_run.return_value.returncode = 0
                
                # Mock the other validation steps to pass
                with patch('ftf_cli.utils.validate_facets_yaml') as mock_validate_yaml, \
                     patch('ftf_cli.utils.validate_facets_tf_vars') as mock_validate_vars:
                    
                    mock_validate_yaml.return_value = True
                    mock_validate_vars.return_value = True
                    
                    # Run the command
                    result = runner.invoke(validate_directory, [temp_dir, '--skip-terraform-validation', 'true'])
                    
                    # Should fail due to provider blocks in nested directory
                    assert result.exit_code != 0
                    assert "Provider blocks are not allowed in module files" in result.output
                    assert "modules/vpc/vpc.tf" in result.output

    def test_validate_directory_with_multiple_nested_provider_blocks(self):
        """Test that validate_directory detects provider blocks in multiple nested locations."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create provider block in root
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Create provider block in first nested directory
            nested_dir1 = os.path.join(temp_dir, "modules", "vpc")
            os.makedirs(nested_dir1)
            nested_tf1 = os.path.join(nested_dir1, "vpc.tf")
            with open(nested_tf1, "w") as f:
                f.write('''
provider "aws" {
  region = "us-east-1"
  alias  = "east"
}

resource "aws_vpc" "nested" {
  cidr_block = "10.0.0.0/16"
}
''')
            
            # Create provider block in second nested directory
            nested_dir2 = os.path.join(temp_dir, "submodules")
            os.makedirs(nested_dir2)
            nested_tf2 = os.path.join(nested_dir2, "database.tf")
            with open(nested_tf2, "w") as f:
                f.write('''
provider "postgresql" {
  host = "localhost"
}

resource "postgresql_database" "test" {
  name = "testdb"
}
''')
            
            variables_tf = os.path.join(temp_dir, "variables.tf")
            with open(variables_tf, "w") as f:
                f.write('''
variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Instance name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "inputs" {
  description = "Inputs"
  type        = object({})
}
''')
            
            facets_yaml = os.path.join(temp_dir, "facets.yaml")
            with open(facets_yaml, "w") as f:
                f.write('''
intent: test-intent
flavor: test-flavor
version: "1.0"
description: Test module for provider validation
clouds:
  - aws
spec:
  type: object
  properties: {}
''')
            
            # Mock external dependencies to focus on provider validation
            with patch('ftf_cli.commands.validate_directory.run') as mock_run:
                # Mock terraform version check to succeed
                mock_run.return_value.returncode = 0
                
                # Mock the other validation steps to pass
                with patch('ftf_cli.utils.validate_facets_yaml') as mock_validate_yaml, \
                     patch('ftf_cli.utils.validate_facets_tf_vars') as mock_validate_vars:
                    
                    mock_validate_yaml.return_value = True
                    mock_validate_vars.return_value = True
                    
                    # Run the command
                    result = runner.invoke(validate_directory, [temp_dir, '--skip-terraform-validation', 'true'])
                    
                    # Should fail due to provider blocks in multiple locations
                    assert result.exit_code != 0
                    assert "Provider blocks are not allowed in module files" in result.output
                    # Should detect all three files with provider blocks
                    assert "main.tf" in result.output
                    assert "modules/vpc/vpc.tf" in result.output
                    assert "submodules/database.tf" in result.output
