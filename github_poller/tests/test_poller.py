import pytest
from github_poller.poller import GithubPoller


class DummyResponse:

    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    import requests

    def fake_get(url, headers=None, params=None):
        # Simulate two commits newer than since_sha
        return DummyResponse([{"sha": "newsha1"}, {"sha": "newsha2"}])

    monkeypatch.setattr(requests, "get", fake_get)


def test_get_new_commits_returns_list_of_shas():
    gp = GithubPoller(owner="SimplifyJobs",
                      repo="New-Grad-Positions",
                      token="fake")
    shas = gp.get_new_commits(since_sha="oldsha")
    assert shas == ["newsha1", "newsha2"]
