import time
from typing import Tuple, List
import requests
from requests.adapters import HTTPAdapter, Retry

from github_poller.parser import DiffParser
from common.models import JobListing

DEFAULT_TIMEOUT = (5, 20)  # (connect, read) seconds


def _timed_get(session: requests.Session, url: str,
               **kwargs) -> requests.Response:
    t0 = time.time()
    try:
        return session.get(url, **kwargs, timeout=DEFAULT_TIMEOUT)
    finally:
        dt = int((time.time() - t0) * 1000)
        print(f"[poller] GET {url} {dt}ms")


class GithubPoller:

    def __init__(self, owner: str, repo: str, token: str, branch: str = "dev"):
        self.owner = owner
        self.repo = repo
        self.branch = branch

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "swe-repo-notify/1.0",
        }
        if token:
            # GitHub accepts either "token" or "Bearer"; keep "token" for PATs
            self.headers["Authorization"] = f"token {token}"

        # Session with retries for transient failures
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_new_commits(self, since_sha: str) -> List[str]:
        """
    Returns newest-first list of SHAs that are newer than `since_sha`.
    """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits"
        params = {"sha": self.branch, "per_page": 100}
        resp = _timed_get(self.session,
                          url,
                          headers=self.headers,
                          params=params)
        resp.raise_for_status()
        commits = resp.json()

        shas = [c["sha"] for c in commits]
        if since_sha and since_sha in shas:
            idx = shas.index(since_sha)
            shas = shas[:idx]  # Newer than last seen
        elif since_sha:
            # Last seen sha not in first page; still process whole page (newest)
            pass
        return shas

    def get_commit_diff(self, sha: str) -> List[str]:
        """
    Returns the patch for .github/scripts/listings.json split into lines.
    """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{sha}"
        resp = _timed_get(self.session, url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        for file in data.get("files", []):
            if file.get("filename",
                        "").endswith("listings.json") and "patch" in file:
                return file["patch"].splitlines()
        return []

    def fetch_new_listings(self,
                           since_sha: str) -> Tuple[List[JobListing], str]:
        """
    Returns (all_new_listings, latest_sha).
    """
        try:
            new_shas = self.get_new_commits(since_sha)
        except requests.RequestException as e:
            print(f"[poller] error get_new_commits: {e}")
            return [], since_sha

        all_jobs: List[JobListing] = []
        for sha in new_shas:
            try:
                diff = self.get_commit_diff(sha)
            except requests.RequestException as e:
                print(f"[poller] error get_commit_diff {sha}: {e}")
                continue
            jobs = DiffParser.parse_added_listings(diff)
            all_jobs.extend(jobs)

        latest_sha = new_shas[0] if new_shas else since_sha
        return all_jobs, latest_sha
