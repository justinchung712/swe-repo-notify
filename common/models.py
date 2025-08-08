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


@dataclass
class UserPreferences:
    subscribe_new_grad: bool
    subscribe_internship: bool
    receive_all: bool  # if True, match everything
    tech_keywords: List[str]  # e.g. ["spring boot", "postgres"]
    role_keywords: List[str]  # e.g. ["backend", "qa"]
    location_keywords: List[str]  # e.g. ["new york", "canada"]
