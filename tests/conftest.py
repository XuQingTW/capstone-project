import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["TESTING"] = "true"
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test_line_token"
os.environ["LINE_CHANNEL_SECRET"] = "test_line_secret"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["POWERBI_CLIENT_ID"] = "test_powerbi_client_id"
os.environ["POWERBI_CLIENT_SECRET"] = "test_powerbi_client_secret"
os.environ["POWERBI_TENANT_ID"] = "test_powerbi_tenant_id"
os.environ["POWERBI_WORKSPACE_ID"] = "test_powerbi_workspace_id"
os.environ["POWERBI_REPORT_ID"] = "test_powerbi_report_id"

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test_line_token")
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test_line_secret")
    monkeypatch.setenv("POWERBI_CLIENT_ID", "test_powerbi_client_id")
    monkeypatch.setenv("POWERBI_CLIENT_SECRET", "test_powerbi_client_secret")
    monkeypatch.setenv("POWERBI_TENANT_ID", "test_powerbi_tenant_id")
    monkeypatch.setenv("POWERBI_WORKSPACE_ID", "test_powerbi_workspace_id")
    monkeypatch.setenv("POWERBI_REPORT_ID", "test_powerbi_report_id")