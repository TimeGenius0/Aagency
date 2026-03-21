from unittest.mock import MagicMock, patch
from linkedin_agent.web import WebClient


def test_fetch_returns_text():
    client = WebClient(openclaw_api_key="fake")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    with patch("linkedin_agent.web.httpx.get", return_value=mock_response):
        result = client.fetch("https://example.com")
    assert "Hello world" in result


def test_fetch_returns_none_after_retries():
    client = WebClient(openclaw_api_key="fake")
    with patch("linkedin_agent.web.httpx.get", side_effect=Exception("timeout")):
        result = client.fetch("https://example.com")
    assert result is None
