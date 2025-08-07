from dataclasses import dataclass
from typing import List, Optional


@dataclass
class JobListing:
    id: str
    date_posted: int
    url: str
    company_name: str
    title: str
    locations: List[str]
    sponsorship: str
    active: bool
    source: str
    date_updated: Optional[int] = None
    company_url: Optional[str] = None
    is_visible: Optional[bool] = None
    category: Optional[str] = None
