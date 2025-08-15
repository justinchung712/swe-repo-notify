import requests
from typing import Tuple, List
from github_poller.parser import DiffParser
from common.models import JobListing


class GithubPoller:

    def __init__(self, owner: str, repo: str, token: str, branch: str = "dev"):
        self.owner = owner
        self.repo = repo
        self.headers = {"Authorization": f"token {token}"}
        self.branch = branch

    def get_new_commits(self, since_sha: str) -> List[str]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits"
        params = {"sha": self.branch, "per_page": 100}
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        commits = resp.json()
        # Collect SHAs until we hit since_sha
        new_shas = []
        for c in commits:
            if c["sha"] == since_sha:
                break
            new_shas.append(c["sha"])
        return new_shas

    def get_commit_diff(self, sha: str) -> List[str]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{sha}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        for file in data.get("files", []):
            if file["filename"].endswith("listings.json") and "patch" in file:
                # Split patch text into lines
                return file["patch"].splitlines()
        return []

    def fetch_new_listings(self,
                           since_sha: str) -> Tuple[List[JobListing], str]:
        """
        Returns (all_new_listings, latest_sha).
        """
        new_shas = self.get_new_commits(since_sha)
        all_jobs: List[JobListing] = []

        for sha in new_shas:
            diff = self.get_commit_diff(sha)
            jobs = DiffParser.parse_added_listings(diff)
            all_jobs.extend(jobs)

        latest_sha = new_shas[0] if new_shas else since_sha
        return all_jobs, latest_sha
