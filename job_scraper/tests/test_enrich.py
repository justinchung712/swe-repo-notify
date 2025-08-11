import pytest
from common.models import JobListing
from job_scraper.enrich import enrich_descriptions


class DummyScraper:

    def __init__(self):
        self.calls = []

    async def fetch_description(self, url):
        self.calls.append(url)

        class JD:

            def __init__(self, url):
                self.url = url
                self.text = f"Desc for {url}"

        return JD(url)


@pytest.mark.asyncio
async def test_enrich_descriptions_sets_text():
    jobs = [
        JobListing(id="1",
                   date_posted=0,
                   url="https://a.com/job1",
                   company_name="A",
                   title="T",
                   locations=[],
                   sponsorship="",
                   active=True,
                   source="src"),
        JobListing(id="2",
                   date_posted=0,
                   url="https://b.com/job2",
                   company_name="B",
                   title="T",
                   locations=[],
                   sponsorship="",
                   active=True,
                   source="src"),
    ]

    scraper = DummyScraper()
    await enrich_descriptions(jobs, scraper, concurrency=2)

    assert all(j.description is not None for j in jobs)
    assert jobs[0].description.startswith("Desc for https://a.com")
    assert set(scraper.calls) == {j.url for j in jobs}
