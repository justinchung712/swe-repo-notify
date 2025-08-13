import os
import pytest
import requests

LIVE = os.getenv("RUN_LIVE_TESTS") == "1"
TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


@pytest.mark.skipif(not LIVE, reason="Set RUN_LIVE_TESTS=1 to run")
def test_commits_endpoint_live():
    headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
    r = requests.get(
        "https://api.github.com/repos/SimplifyJobs/New-Grad-Positions/commits?per_page=3",
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    assert "sha" in data[0]
