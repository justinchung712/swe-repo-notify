import re, json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import httpx
from bs4 import BeautifulSoup


# Factory wrapper so we can monkeypatch in tests
def AsyncClientFactory():
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5, read=10, write=10, pool=5),
        headers={"User-Agent": "swe-repo-notify/1.0"},
        http2=True,
        follow_redirects=True,
    )


@dataclass
class JobDescription:
    url: str
    text: str
    source: str
    fetched_at: datetime


def normalize_url(url: str) -> str:
    # Common "application" endings -> description page
    url = re.sub(r"/application/?$", "", url)
    url = re.sub(r"/apply/?$", "", url)
    return url


def detect_source(url: str) -> str:
    host = url.split("/")[2].lower()
    if "greenhouse.io" in host: return "greenhouse"
    if "ashbyhq.com" in host: return "ashby"
    if "lever.co" in host: return "lever"
    if "icims.com" in host: return "icims"
    if "workday" in host or "myworkdayjobs.com" in host or re.search(
            r"\bwd\d+\.", host):
        return "workday"
    if "tesla.com" in host: return "tesla"
    if "bytedance.com" in host or "lifeattiktok.com" in host:
        return "bytedance"
    return "generic"


async def _fetch_html(url: str) -> str:
    async with AsyncClientFactory() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _extract_text_static(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Platform-ish selectors first
    candidates = [
        "[data-testid='JobDescription']",
        "[data-qa='job-description']",
        "div.job-description",
        "section.job-description",
        "#content",
        ".content",
        "article",
        "main",
    ]
    for sel in candidates:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(separator="\n", strip=True)

    # Try ld+json description
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
            if isinstance(data, dict) and "description" in data:
                return BeautifulSoup(data["description"],
                                     "html.parser").get_text(" ", strip=True)
        except Exception:
            pass

    # Fallback: page visible text
    return soup.get_text("\n", strip=True)


async def _fetch_headless_text(url: str) -> str:
    # Stub for future: Playwright with short waits for known selectors.
    # For now, we skip headless in tests; wire it when deploying.
    return ""


class JobScraper:

    def __init__(self,
                 cache: Optional[object],
                 use_headless_fallback: bool = True):
        self.cache = cache
        self.use_headless = use_headless_fallback

    async def fetch_description(self, url: str) -> JobDescription:
        nurl = normalize_url(url)
        source = detect_source(nurl)

        # Cache read
        if self.cache:
            cached = self.cache.get(nurl)
            if cached:
                return cached

        html = await _fetch_html(nurl)
        text = _extract_text_static(html)

        # Optionally try headless if too little text
        if self.use_headless and len(text) < 500:
            try:
                htext = await _fetch_headless_text(nurl)
                if len(htext) > len(text):
                    text = htext
            except Exception:
                pass

        jd = JobDescription(
            url=nurl,
            text=text,
            source=source,
            fetched_at=datetime.now(timezone.utc),
        )

        # Cache write
        if self.cache and len(text) >= 50:
            self.cache.put(jd)

        return jd
