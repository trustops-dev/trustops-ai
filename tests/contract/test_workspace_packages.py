"""Check that workspace distributions install with their intended import names."""

from importlib import import_module
from importlib.metadata import distribution
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("distribution_name", "module_name"),
    [
        ("trustops-contracts", "trustops_contracts"),
        ("trustops-instrumentation-sdk", "trustops_sdk"),
        ("trustops-platform-core", "trustops_platform"),
        ("trustops-reliability-engine", "trustops_reliability"),
        ("trustops-governance-engine", "trustops_governance"),
        ("trustops-mlops", "trustops_mlops"),
        ("trustops-api", "trustops_api"),
        ("trustops-procurement-agent", "trustops_procurement_agent"),
        ("trustops-rag-assistant", "trustops_rag_assistant"),
    ],
)
def test_workspace_package_is_installed(
    distribution_name: str,
    module_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Imports must work outside the checkout, without adding src paths to sys.path."""
    monkeypatch.chdir(tmp_path)
    installed = distribution(distribution_name)
    module = import_module(module_name)

    assert installed.metadata["Name"] == distribution_name
    assert module.__file__ is not None
    assert Path(module.__file__).is_file()
