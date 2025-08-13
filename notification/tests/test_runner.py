import sqlite3
import pytest
from persistence.db import init_db
from persistence.repositories import (UserRepository, RepoStateRepository,
                                      SentNotificationsRepository)
from common.models import UserPreferences, JobListing, UserContact
from notification.service import NotificationService
from notification.runner import run_all_repos_once
from notification.orchestrator import NEW_GRAD_REPO
from job_scraper.scraper import JobScraper

# Fakes


class FakeSender:

    def __init__(self):
        self.emails = []
        self.sms = []

    def send_email(self, to_addr, subject, html_body, text_body):
        self.emails.append((to_addr, subject, text_body))

    def send_sms(self, to_number, text_body):
        self.sms.append((to_number, text_body))


class DummyScraper:

    async def fetch_description(self, url: str):

        class JD:

            def __init__(self, url):
                self.url = url
                self.text = "kubernetes spring boot"

        return JD(url)


class FakePollerNG:
    """Monkeypatch target for GithubPoller in runner: New Grad repo."""

    def __init__(self, *args, **kwargs):
        pass

    def fetch_new_listings(self, since_sha):
        jobs = [
            JobListing(
                id="job1",
                date_posted=0,
                url="https://ex.com/1",
                company_name="Acme",
                title="Backend Engineer",
                locations=["Remote"],
                sponsorship="None",
                active=True,
                source="Simplify",
            ),
            JobListing(
                id="job2",
                date_posted=0,
                url="https://ex.com/2",
                company_name="Beta",
                title="DevOps Engineer",
                locations=["Remote"],
                sponsorship="None",
                active=True,
                source="Simplify",
            ),
        ]
        return jobs, "sha-ng-2"


class FakePollerIntern:
    """Monkeypatch target for GithubPoller in runner: Internships repo."""

    def __init__(self, *args, **kwargs):
        pass

    def fetch_new_listings(self, since_sha):
        # No new jobs this time
        return [], since_sha or "sha-int-0"


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def repos(conn):
    return (
        UserRepository(conn),
        RepoStateRepository(conn),
        SentNotificationsRepository(conn),
    )


def test_run_all_repos_once_hydrates_users_sends_batched_and_updates_sha(
        monkeypatch, repos):
    user_repo, state_repo, sent_repo = repos

    # Seed one verified user who wants New Grad email summaries and matches everything
    prefs = UserPreferences(
        subscribe_new_grad=True,
        subscribe_internship=False,
        receive_all=True,
        tech_keywords=[],
        role_keywords=[],
        location_keywords=[],
    )
    user_repo.create_user(
        user_id="u1",
        email="dev@user.com",
        phone=None,
        is_verified=True,
        prefs=prefs,
        notify_email=True,
        notify_sms=False,
    )

    # Monkeypatch the GithubPoller used inside the runner to use the fakes
    import notification.runner as runner_mod

    def fake_ng(owner, repo, token=""):
        assert owner == "SimplifyJobs" and repo == "New-Grad-Positions"
        return FakePollerNG()

    def fake_intern(owner, repo, token=""):
        assert owner == "SimplifyJobs" and repo == "Summer2026-Internships"
        return FakePollerIntern()

    monkeypatch.setattr(
        runner_mod,
        "GithubPoller",
        lambda owner, repo, token="": fake_ng(owner, repo, token)
        if repo == "New-Grad-Positions" else fake_intern(owner, repo, token))

    # Fake notifier + real NotificationService
    sender = FakeSender()
    notifier = NotificationService(
        sender, edit_link_builder=lambda u: "http://edit/link")

    # Dummy scraper (async)
    scraper = JobScraper(cache=None, use_headless_fallback=False)
    # Monkeypatch the scraper instance's fetcher via attribute assignment
    scraper.fetch_description = DummyScraper(
    ).fetch_description  # Type: ignore

    stats = run_all_repos_once(
        user_repo=user_repo,
        state_repo=state_repo,
        sent_repo=sent_repo,
        notifier=notifier,
        scraper=scraper,
        github_token="",  # Not used by fakes
    )

    # Assertions: one email sent with both jobs; sha updated
    assert len(sender.emails) == 1
    to, subject, text = sender.emails[0]
    assert to == "dev@user.com"
    assert "2 new matches" in subject.lower()
    assert "Backend Engineer" in text and "DevOps Engineer" in text

    # Repo state advanced for NG
    assert state_repo.get_last_sha(NEW_GRAD_REPO) == "sha-ng-2"

    # Dedup works: second run should not re-send
    sender.emails.clear()
    stats2 = run_all_repos_once(
        user_repo=user_repo,
        state_repo=state_repo,
        sent_repo=sent_repo,
        notifier=notifier,
        scraper=scraper,
        github_token="",
    )
    assert sender.emails == []  # Nothing new sent
