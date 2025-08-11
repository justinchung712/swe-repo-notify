import asyncio
from typing import List, Callable
from common.models import JobListing
from job_scraper.scraper import JobScraper


async def enrich_descriptions(jobs: List[JobListing],
                              scraper: JobScraper,
                              concurrency: int = 6) -> None:
    sem = asyncio.Semaphore(concurrency)

    async def one(job: JobListing):
        async with sem:
            try:
                jd = await scraper.fetch_description(job.url)
                job.description = jd.text
            except Exception:
                # Leave description None on failure
                job.description = None

    await asyncio.gather(*(one(j) for j in jobs))
