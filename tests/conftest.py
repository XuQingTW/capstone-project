import os
import sys
import pytest

# Add the parent directory to sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ..)))

# Set test environment variables
@pytest.fixture(autouse=True)
def set_test_env(monkeypatch)
    monkeypatch.setenv(OPENAI_API_KEY, test_openai_key)
    monkeypatch.setenv(LINE_CHANNEL_ACCESS_TOKEN, test_line_token)
    monkeypatch.setenv(LINE_CHANNEL_SECRET, test_line_secret)
    monkeypatch.setenv(POWERBI_CLIENT_ID, test_powerbi_client_id)
    monkeypatch.setenv(POWERBI_CLIENT_SECRET, test_powerbi_client_secret)
    monkeypatch.setenv(POWERBI_TENANT_ID, test_powerbi_tenant_id)
    monkeypatch.setenv(POWERBI_WORKSPACE_ID, test_powerbi_workspace_id)
    monkeypatch.setenv(POWERBI_REPORT_ID, test_powerbi_report_id)