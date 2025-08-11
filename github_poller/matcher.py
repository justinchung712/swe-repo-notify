from typing import Iterable
from common.models import JobListing, UserPreferences


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _any_keyword_in_text(keywords: Iterable[str], text: str) -> bool:
    text = _norm(text)
    for kw in keywords:
        if kw and _norm(kw) in text:
            return True
    return False


def _locations_match(job_locations: Iterable[str],
                     location_keywords: Iterable[str]) -> bool:
    # Require at least one keyword to be contained in at least one job location
    # e.g., "new york" matches "New York, NY"; "remote" matches "Remote"
    locs = [_norm(l) for l in (job_locations or [])]
    kws = [_norm(k) for k in (location_keywords or []) if k]
    if not kws:
        return True  # No location gate
    if not locs:
        return False  # User asked for locations but job has none => fail
    for loc in locs:
        for kw in kws:
            if kw in loc:
                return True
    return False


class MatchingEngine:

    @staticmethod
    def matches(job: JobListing, prefs: UserPreferences) -> bool:
        # 0) Match everything if user opted in
        if prefs.receive_all:
            return True

        # 1) Location gate (priority)
        if not _locations_match(job.locations, prefs.location_keywords):
            return False

        # 2) Build searchable blob for role/tech
        desc = (job.description or "")
        blob = f"{job.title} {job.company_name} {desc}".lower()

        # 3) Role keyword match
        if _any_keyword_in_text(prefs.role_keywords, blob):
            return True

        # 4) Tech keyword match
        if _any_keyword_in_text(prefs.tech_keywords, blob):
            return True

        # 5) If user provided role/tech lists and none matched, it's a no.
        #    If they provided neither (both empty), treat as "no constraints" -> match.
        if not prefs.role_keywords and not prefs.tech_keywords:
            return True

        return False
