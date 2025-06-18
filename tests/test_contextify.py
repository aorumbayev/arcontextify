"""Pytest unit tests for arcontextify tool."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.arcontextify.code_generator import generate_mcp_server
from src.arcontextify.arc56_parser import parse_arc56_file


@pytest.fixture(scope="session")
def artifacts_dir() -> Path:
    """Return the artifacts directory path."""
    return Path(__file__).parent.parent / "artifacts"


@pytest.fixture(scope="session")
def temp_output_dir() -> Generator[Path, None, None]:
    """Create and cleanup temporary output directory."""
    with tempfile.TemporaryDirectory(prefix="contextify_test_") as temp_dir:
        yield Path(temp_dir)


def get_arc56_files(artifacts_dir: Path) -> list[Path]:
    """Get all ARC-56 JSON files from artifacts directory."""
    return list(artifacts_dir.glob("*.arc56.json"))


def pytest_generate_tests(metafunc):
    """Parametrize tests with all ARC-56 files in artifacts folder."""
    if "arc56_file" in metafunc.fixturenames:
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        arc56_files = get_arc56_files(artifacts_dir)

        if not arc56_files:
            pytest.skip("No ARC-56 files found in artifacts directory")

        # Create test IDs from filenames (without .arc56.json extension)
        test_ids = [f.stem.replace(".arc56", "") for f in arc56_files]

        metafunc.parametrize("arc56_file", arc56_files, ids=test_ids)


class TestARCContextifyGeneration:
    """Test arcontextify ARC-56 to MCP server generation."""

    def test_arc56_file_is_valid_json(self, arc56_file: Path) -> None:
        """Test that ARC-56 file is valid JSON."""
        with open(arc56_file, encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {arc56_file.name}: {e}")

    def test_arc56_file_has_required_fields(self, arc56_file: Path) -> None:
        """Test that ARC-56 file has required fields."""
        with open(arc56_file, encoding="utf-8") as f:
            data = json.load(f)

        required_fields = ["name", "methods"]
        for field in required_fields:
            assert field in data, (
                f"Missing required field '{field}' in {arc56_file.name}"
            )

        assert isinstance(data["methods"], list), (
            f"'methods' field must be a list in {arc56_file.name}"
        )

    def test_arc56_parser_can_parse_file(self, arc56_file: Path) -> None:
        """Test that arc56_parser can successfully parse the file."""
        try:
            contract = parse_arc56_file(str(arc56_file))
            assert contract.name, f"Contract name is empty for {arc56_file.name}"
            assert hasattr(contract, "methods"), (
                f"Contract missing methods attribute for {arc56_file.name}"
            )
        except Exception as e:
            pytest.fail(f"Failed to parse {arc56_file.name}: {e}")

    def test_generate_mcp_server(self, arc56_file: Path, temp_output_dir: Path) -> None:
        """Test MCP server generation from ARC-56 file."""
        try:
            project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))

            # Verify project directory was created
            assert project_dir.exists(), (
                f"Project directory not created for {arc56_file.name}"
            )
            assert project_dir.is_dir(), (
                f"Project path is not a directory for {arc56_file.name}"
            )

            # Verify basic project structure
            expected_files = [
                "pyproject.toml",
                "README.md",
                "src",
            ]

            for expected_file in expected_files:
                file_path = project_dir / expected_file
                assert file_path.exists(), (
                    f"Missing {expected_file} in generated project for {arc56_file.name}"
                )

            # Verify src directory structure
            src_dir = project_dir / "src"
            assert src_dir.is_dir(), f"src directory not found for {arc56_file.name}"

            # Find the package directory (should be named after the contract)
            package_dirs = [
                d
                for d in src_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
            assert len(package_dirs) == 1, (
                f"Expected exactly one package directory in src/ for {arc56_file.name}"
            )

            package_dir = package_dirs[0]
            expected_package_files = ["__init__.py", "server.py"]

            for expected_file in expected_package_files:
                file_path = package_dir / expected_file
                assert file_path.exists(), (
                    f"Missing {expected_file} in package for {arc56_file.name}"
                )

        except Exception as e:
            pytest.fail(f"Failed to generate MCP server for {arc56_file.name}: {e}")

    def test_generated_project_has_valid_pyproject_toml(
        self, arc56_file: Path, temp_output_dir: Path
    ) -> None:
        """Test that generated project has valid pyproject.toml."""
        project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))
        pyproject_path = project_dir / "pyproject.toml"

        assert pyproject_path.exists(), f"pyproject.toml missing for {arc56_file.name}"

        # Try to parse it as TOML (basic validation)
        try:
            # Try Python 3.11+ tomllib first
            import tomllib
        except ImportError:
            # Fallback for Python < 3.11
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                pytest.skip("No TOML library available for validation")

        with open(pyproject_path, "rb") as f:
            try:
                toml_data = tomllib.load(f)
                assert "project" in toml_data, (
                    f"Missing [project] section in pyproject.toml for {arc56_file.name}"
                )
                assert "name" in toml_data["project"], (
                    f"Missing project name in pyproject.toml for {arc56_file.name}"
                )
            except Exception as e:
                pytest.fail(f"Invalid pyproject.toml for {arc56_file.name}: {e}")

    def test_generated_server_is_valid_python(
        self, arc56_file: Path, temp_output_dir: Path
    ) -> None:
        """Test that generated server.py is valid Python syntax."""
        project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))

        # Find the server.py file
        src_dir = project_dir / "src"
        package_dirs = [
            d for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        package_dir = package_dirs[0]
        server_path = package_dir / "server.py"

        assert server_path.exists(), f"server.py missing for {arc56_file.name}"

        # Try to compile the Python file
        with open(server_path, encoding="utf-8") as f:
            source_code = f.read()

        try:
            compile(source_code, str(server_path), "exec")
        except SyntaxError as e:
            pytest.fail(
                f"Invalid Python syntax in generated server.py for {arc56_file.name}: {e}"
            )

    def test_uv_sync_succeeds(self, arc56_file: Path, temp_output_dir: Path) -> None:
        """Test that 'uv sync' succeeds in the generated project."""
        project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))

        # Check if uv is available
        try:
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("uv not available - skipping uv sync test")

        # Run uv sync in the project directory
        try:
            subprocess.run(
                ["uv", "sync"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Verify that uv.lock was created
            lock_file = project_dir / "uv.lock"
            assert lock_file.exists(), (
                f"uv.lock not created after sync for {arc56_file.name}"
            )

        except subprocess.CalledProcessError as e:
            pytest.fail(f"uv sync failed for {arc56_file.name}: {e.stderr}")
        except subprocess.TimeoutExpired:
            pytest.fail(f"uv sync timed out for {arc56_file.name}")

    def test_generated_server_can_be_imported(
        self, arc56_file: Path, temp_output_dir: Path
    ) -> None:
        """Test that the generated server can be imported successfully."""
        project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))

        # Add the project src directory to Python path
        src_dir = project_dir / "src"
        sys.path.insert(0, str(src_dir))

        try:
            # Find the package name
            package_dirs = [
                d
                for d in src_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
            package_name = package_dirs[0].name

            # Try to import the server module
            import importlib

            server_module = importlib.import_module(f"{package_name}.server")

            # Verify it has expected attributes
            assert hasattr(server_module, "mcp"), (
                f"Generated server missing 'mcp' attribute for {arc56_file.name}"
            )

        except ImportError as e:
            pytest.fail(f"Failed to import generated server for {arc56_file.name}: {e}")
        finally:
            # Clean up sys.path
            if str(src_dir) in sys.path:
                sys.path.remove(str(src_dir))


class TestContextifyIntegration:
    """Integration tests for the full arcontextify workflow."""

    def test_full_workflow_all_artifacts(
        self, artifacts_dir: Path, temp_output_dir: Path
    ) -> None:
        """Test the complete workflow for all artifacts."""
        arc56_files = get_arc56_files(artifacts_dir)

        if not arc56_files:
            pytest.skip("No ARC-56 files found in artifacts directory")

        generated_projects = []

        for arc56_file in arc56_files:
            try:
                # Generate MCP server
                project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))
                generated_projects.append((arc56_file.name, project_dir))

                # Verify basic structure
                assert project_dir.exists()
                assert (project_dir / "pyproject.toml").exists()
                assert (project_dir / "src").exists()

            except Exception as e:
                pytest.fail(f"Workflow failed for {arc56_file.name}: {e}")

        # Verify we generated the expected number of projects
        assert len(generated_projects) == len(arc56_files)

        # Verify all projects have unique names
        project_names = [name for name, _ in generated_projects]
        assert len(project_names) == len(set(project_names)), (
            "Duplicate project names generated"
        )

    @pytest.mark.slow
    def test_uv_sync_all_generated_projects(
        self, artifacts_dir: Path, temp_output_dir: Path
    ) -> None:
        """Test uv sync on all generated projects (marked as slow test)."""
        # Check if uv is available
        try:
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("uv not available - skipping uv sync integration test")

        arc56_files = get_arc56_files(artifacts_dir)

        if not arc56_files:
            pytest.skip("No ARC-56 files found in artifacts directory")

        sync_results = []

        for arc56_file in arc56_files:
            project_dir = generate_mcp_server(str(arc56_file), str(temp_output_dir))

            try:
                subprocess.run(
                    ["uv", "sync"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                sync_results.append((arc56_file.name, True, ""))

            except subprocess.CalledProcessError as e:
                sync_results.append((arc56_file.name, False, e.stderr))
            except subprocess.TimeoutExpired:
                sync_results.append((arc56_file.name, False, "Timeout"))

        # Report results
        failed_syncs = [
            (name, error) for name, success, error in sync_results if not success
        ]

        if failed_syncs:
            error_report = "\n".join(
                [f"  {name}: {error}" for name, error in failed_syncs]
            )
            pytest.fail(f"uv sync failed for projects:\n{error_report}")


if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v"])
