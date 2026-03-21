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


def test_search_returns_text(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_result = MagicMock()
    mock_result.text = "AI trends 2026: agents everywhere."
    mock_cmdop.agent.run.return_value = mock_result
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.search("AI LinkedIn trends")
    assert result is not None
    assert "AI" in result


def test_search_returns_none_on_failure(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_cmdop.agent.run.side_effect = Exception("API error")
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.search("AI LinkedIn trends")
    assert result is None


def test_image_search_returns_dict(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_result = MagicMock()
    mock_result.data = MagicMock(
        url="https://unsplash.com/photo.jpg",
        source_domain="unsplash.com",
        photographer="Jane Doe"
    )
    mock_cmdop.agent.run.return_value = mock_result
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.image_search("AI robot office")
    assert result["url"] == "https://unsplash.com/photo.jpg"
    assert result["photographer"] == "Jane Doe"


def test_image_search_returns_none_on_failure(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_cmdop.agent.run.side_effect = Exception("timeout")
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.image_search("AI robot office")
    assert result is None
