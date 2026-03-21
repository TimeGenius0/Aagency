# linkedin_agent/web.py
from __future__ import annotations
import time
import httpx
from bs4 import BeautifulSoup


class WebClient:
    def __init__(self, openclaw_api_key: str):
        self._api_key = openclaw_api_key
        self._cmdop = None  # lazy init on first search/image_search call

    def _get_cmdop(self):
        if self._cmdop is None:
            from openclaw import OpenClaw
            self._cmdop = OpenClaw.remote(api_key=self._api_key)
        return self._cmdop

    def fetch(self, url: str) -> str | None:
        """Fetch a URL and return readable text. Returns None on final failure."""
        for attempt in range(3):
            try:
                resp = httpx.get(url, timeout=15, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def search(self, query: str) -> str | None:
        """Web search via CMDOP agent. Returns plain-text summary (max 200 words).
        Returns None on all retry attempts."""
        prompt = (
            f"Search the web for: {query}\n"
            f"Return a concise summary (max 200 words) of the most relevant findings. "
            f"Focus on recent, factual content."
        )
        for attempt in range(3):
            try:
                client = self._get_cmdop()
                result = client.agent.run(prompt)
                return result.text
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def image_search(self, query: str) -> dict | None:
        """Find a relevant image via CMDOP agent. Returns {url, source_domain, photographer} or None."""
        from pydantic import BaseModel

        class ImageResult(BaseModel):
            url: str
            source_domain: str
            photographer: str | None = None

        prompt = (
            f"Find a high-quality, freely usable image for: {query}\n"
            f"Prefer images from Unsplash, Pexels, or Pixabay. "
            f"Return the direct image URL, the source domain, and photographer name if available."
        )
        for attempt in range(3):
            try:
                client = self._get_cmdop()
                result = client.agent.run(prompt, output_model=ImageResult)
                if result.data:
                    return {
                        "url": result.data.url,
                        "source_domain": result.data.source_domain,
                        "photographer": result.data.photographer,
                    }
                return None
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None
