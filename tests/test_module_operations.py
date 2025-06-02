import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from ftf_cli.operations import (
    register_module,
    publish_module,
    ModuleOperationError,
    cleanup_terraform_files,
    create_module_zip,
)


class TestModuleOperations:

    def test_cleanup_terraform_files(self):
        """Test that terraform files are properly cleaned up"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test terraform files
            terraform_dir = os.path.join(temp_dir, ".terraform")
            os.makedirs(terraform_dir)

            lock_file = os.path.join(temp_dir, ".terraform.lock.hcl")
            with open(lock_file, "w") as f:
                f.write("test")

            # Cleanup should remove these files
            cleanup_terraform_files(temp_dir)

            assert not os.path.exists(terraform_dir)
            assert not os.path.exists(lock_file)

    def test_create_module_zip(self):
        """Test module zip creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            zip_path = create_module_zip(temp_dir)

            try:
                assert os.path.exists(zip_path)
                assert zip_path.endswith(".zip")
            finally:
                if os.path.exists(zip_path):
                    os.remove(zip_path)

    @patch("requests.post")
    def test_register_module_success(self, mock_post):
        """Test successful module registration"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create facets.yaml
            facets_file = os.path.join(temp_dir, "facets.yaml")
            with open(facets_file, "w") as f:
                f.write("intent: test\nflavor: default\nversion: 1.0\n")

            # Should not raise an exception
            register_module(
                control_plane_url="https://test.example.com",
                username="testuser",
                token="testtoken",
                path=temp_dir,
            )

            # Verify the request was made
            mock_post.assert_called_once()

    @patch("requests.post")
    def test_register_module_error(self, mock_post):
        """Test module registration error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Bad Request"}
        mock_post.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create facets.yaml
            facets_file = os.path.join(temp_dir, "facets.yaml")
            with open(facets_file, "w") as f:
                f.write("intent: test\nflavor: default\nversion: 1.0\n")

            with pytest.raises(ModuleOperationError):
                register_module(
                    control_plane_url="https://test.example.com",
                    username="testuser",
                    token="testtoken",
                    path=temp_dir,
                )

    @patch("requests.post")
    def test_publish_module_success(self, mock_post):
        """Test successful module publishing"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Should not raise an exception
        publish_module(
            control_plane_url="https://test.example.com",
            username="testuser",
            token="testtoken",
            intent="test",
            flavor="default",
            version="1.0",
        )

        # Verify the request was made
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_publish_module_error(self, mock_post):
        """Test module publishing error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal Server Error"}
        mock_post.return_value = mock_response

        with pytest.raises(ModuleOperationError):
            publish_module(
                control_plane_url="https://test.example.com",
                username="testuser",
                token="testtoken",
                intent="test",
                flavor="default",
                version="1.0",
            )

    def test_register_module_missing_facets_yaml(self):
        """Test registration fails when facets.yaml is missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(
                ModuleOperationError, match="facets.yaml file not found"
            ):
                register_module(
                    control_plane_url="https://test.example.com",
                    username="testuser",
                    token="testtoken",
                    path=temp_dir,
                )

    def test_register_module_invalid_path(self):
        """Test registration fails with invalid path"""
        with pytest.raises(
            ModuleOperationError, match="does not exist or is not a directory"
        ):
            register_module(
                control_plane_url="https://test.example.com",
                username="testuser",
                token="testtoken",
                path="/nonexistent/path",
            )

    def test_publish_module_missing_args(self):
        """Test publishing fails with missing arguments"""
        with pytest.raises(ModuleOperationError, match="Missing required arguments"):
            publish_module(
                control_plane_url="",
                username="testuser",
                token="testtoken",
                intent="test",
                flavor="default",
                version="1.0",
            )
