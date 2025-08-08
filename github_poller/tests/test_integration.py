import pytest
from github_poller.poller import GithubPoller


class FakePoller(GithubPoller):

    def __init__(self):
        super().__init__("owner", "repo", token="t")

    def get_new_commits(self, since_sha):
        return ["sha2", "sha1"]  # sha2 is newer than sha1

    def get_commit_diff(self, sha):
        # Return one simple added listing per commit
        if sha == "sha1":
            return [
                '+{',
                '+   "company_name": "A",',
                '+   "id": "id1",',
                '+   "title": "T1",',
                '+   "url": "u1",',
                '+   "date_posted": "1111111111",',
                '+   "locations": [',
                '+       "Remote in UK",',
                '+       "New York, NY"',
                '+   ],',
                '+   "sponsorship": "Other",',
                '+   "active": "true",',
                '+   "source": "YoursTruly"',
                '+}',
            ]
        else:
            return [
                '+{',
                '+   "company_name": "B",',
                '+   "id": "id2",',
                '+   "title": "T2",',
                '+   "url": "u2",',
                '+   "date_posted": "2222222222",',
                '+   "locations": [',
                '+       "Bellevue, WA",',
                '+       "Boise, ID"',
                '+   ],',
                '+   "sponsorship": "U.S. Citizenship is Required",',
                '+   "active": "true",',
                '+   "source": "Another"',
                '+}',
            ]


def test_fetch_new_listings_combines_and_returns_latest_sha():
    p = FakePoller()
    jobs, latest = p.fetch_new_listings(since_sha="old")
    assert latest == "sha2"
    assert len(jobs) == 2
    assert [j.id for j in jobs] == ["id2", "id1"]
