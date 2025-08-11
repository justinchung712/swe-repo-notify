import pytest
from job_scraper.scraper import JobScraper, JobDescription, normalize_url, detect_source


@pytest.mark.asyncio
async def test_ashby_application_rewrite_and_extract(monkeypatch):
    # Original 'application' link -> normalize to base job url
    url = "https://jobs.ashbyhq.com/ramp/8c...f4da/application"
    normalized = "https://jobs.ashbyhq.com/ramp/8c...f4da"

    class FakeResp:
        status_code = 200
        text = """
        <html><body>
          <div data-testid="JobDescription">
            <p>We’re looking for a Backend Engineer with Python, Postgres, and AWS.</p>
          </div>
        </body></html>
        """

        def raise_for_status(self):
            pass

    class FakeClient:

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, **kwargs):
            assert url == normalized
            return FakeResp()

    import job_scraper.scraper as scr
    monkeypatch.setattr(scr, "AsyncClientFactory", lambda: FakeClient())

    scraper = JobScraper(cache=None, use_headless_fallback=False)
    jd = await scraper.fetch_description(url)
    assert "Backend Engineer" in jd.text
    assert jd.url == normalized
    assert detect_source(jd.url) == "ashby"


@pytest.mark.asyncio
async def test_generic_fallback_extracts_visible_text(monkeypatch):
    url = "https://example.com/job/123"

    class FakeResp:
        status_code = 200
        text = "<html><body><main><h1>Title</h1><div class='job-description'>Kubernetes, Go, gRPC</div></main></body></html>"

        def raise_for_status(self):
            pass

    class FakeClient:

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, **kwargs):
            return FakeResp()

    import job_scraper.scraper as scr
    monkeypatch.setattr(scr, "AsyncClientFactory", lambda: FakeClient())

    scraper = JobScraper(cache=None, use_headless_fallback=False)
    jd = await scraper.fetch_description(url)
    assert "Kubernetes" in jd.text
    assert jd.source == "generic"


def test_normalize_basic_rules():
    assert normalize_url("https://jobs.ashbyhq.com/x/y/application"
                         ) == "https://jobs.ashbyhq.com/x/y"
    assert normalize_url("https://boards.greenhouse.io/x/jobs/123/apply"
                         ) == "https://boards.greenhouse.io/x/jobs/123"
    assert normalize_url(
        "https://jobs.lever.co/x/123/apply") == "https://jobs.lever.co/x/123"
