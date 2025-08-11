import sqlite3
import pytest
from job_scraper.scraper import JobScraper
from persistence.db import init_db
from persistence.repositories import RepoStateRepository, SentNotificationsRepository
from common.models import JobListing, UserPreferences, UserContact
from notification.service import NotificationService
from notification.orchestrator import run_poll_for_repo


class FakeSender:

    def __init__(self):
        self.emails = []
        self.sms = []

    def send_email(self, to_addr, subject, html_body, text_body):
        self.emails.append((to_addr, subject, text_body))

    def send_sms(self, to_number, text_body):
        self.sms.append((to_number, text_body))


class FakePoller:

    def __init__(self, jobs, latest_sha):
        self.jobs = jobs
        self.latest_sha = latest_sha

    def fetch_new_listings(self, since_sha):
        # Ignore since_sha in tests; return fixed set
        return (self.jobs, self.latest_sha)


class DummyScraper:

    async def fetch_description(self, url: str):

        class JD:

            def __init__(self, url):
                self.url = url
                self.text = "kubernetes spring boot"

        return JD(url)


def J(i, title, company="Acme", url=None, locs=None):
    return JobListing(
        id=str(i),
        date_posted=0,
        url=url or f"https://ex.com/{i}",
        company_name=company,
        title=title,
        locations=locs or ["Remote"],
        sponsorship="None",
        active=True,
        source="Simplify",
    )


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def test_orchestrator_batches_and_updates_sha(conn):
    repo_name = "SimplifyJobs/New-Grad-Positions"
    repo_label = "New Grad"

    jobs = [J(1, "Backend Engineer"), J(2, "DevOps Engineer")]
    poller = FakePoller(jobs, latest_sha="sha2")

    sender = FakeSender()
    notifier = NotificationService(
        sender, edit_link_builder=lambda u: "https://edit/link")
    sent_repo = SentNotificationsRepository(conn)
    state_repo = RepoStateRepository(conn)

    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=True,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    users = [
        UserContact(id="u1",
                    email="a@b.com",
                    phone=None,
                    is_verified=True,
                    notify_email=True,
                    notify_sms=False,
                    prefs=prefs)
    ]

    stats = run_poll_for_repo(repo_name=repo_name,
                              repo_label=repo_label,
                              poller=poller,
                              users=users,
                              sent_repo=sent_repo,
                              state_repo=state_repo,
                              notifier=notifier,
                              scraper=DummyScraper())

    # One email with two jobs; sha updated
    assert len(sender.emails) == 1
    to, subject, text = sender.emails[0]
    assert to == "a@b.com"
    assert "2 new matches" in subject.lower()
    assert "Backend Engineer" in text and "DevOps Engineer" in text
    assert state_repo.get_last_sha(repo_name) == "sha2"
    # Stats sanity
    assert stats["users_notified"] == 1
    assert stats["jobs_considered"] == 2
    assert stats["jobs_sent_total"] == 2


def test_orchestrator_respects_internship_subscription(conn):
    repo_name = "SimplifyJobs/New-Grad-Positions"
    jobs = [J(1, "Backend Engineer")]
    poller = FakePoller(jobs, latest_sha="shaX")

    sender = FakeSender()
    notifier = NotificationService(
        sender, edit_link_builder=lambda u: "https://edit/link")
    sent_repo = SentNotificationsRepository(conn)
    state_repo = RepoStateRepository(conn)

    # User only subscribes to internships, so should not receive for New Grad repo
    prefs = UserPreferences(subscribe_new_grad=False,
                            subscribe_internship=True,
                            receive_all=True,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    users = [
        UserContact(id="u2",
                    email="b@b.com",
                    phone=None,
                    is_verified=True,
                    notify_email=True,
                    notify_sms=False,
                    prefs=prefs)
    ]

    run_poll_for_repo(repo_name=repo_name,
                      repo_label="New Grad",
                      poller=poller,
                      users=users,
                      sent_repo=sent_repo,
                      state_repo=state_repo,
                      notifier=notifier,
                      scraper=DummyScraper())

    assert sender.emails == []  # No sends


def test_orchestrator_respects_newgrad_subscription(conn):
    repo_name = "SimplifyJobs/Summer2026-Internships"
    jobs = [J(1, "Backend Engineer")]
    poller = FakePoller(jobs, latest_sha="shaX")

    sender = FakeSender()
    notifier = NotificationService(
        sender, edit_link_builder=lambda u: "https://edit/link")
    sent_repo = SentNotificationsRepository(conn)
    state_repo = RepoStateRepository(conn)

    # User only subscribes to new grad positions, so should not receive for Internships repo
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=True,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    users = [
        UserContact(id="u2",
                    email="b@b.com",
                    phone=None,
                    is_verified=True,
                    notify_email=True,
                    notify_sms=False,
                    prefs=prefs)
    ]

    run_poll_for_repo(repo_name=repo_name,
                      repo_label="New Grad",
                      poller=poller,
                      users=users,
                      sent_repo=sent_repo,
                      state_repo=state_repo,
                      notifier=notifier,
                      scraper=DummyScraper())

    assert sender.emails == []  # No sends


def test_orchestrator_dedup_second_run(conn):
    repo_name = "SimplifyJobs/New-Grad-Positions"
    jobs = [J(1, "Backend Engineer")]
    poller = FakePoller(jobs, latest_sha="shaA")

    sender = FakeSender()
    notifier = NotificationService(
        sender, edit_link_builder=lambda u: "https://edit/link")
    sent_repo = SentNotificationsRepository(conn)
    state_repo = RepoStateRepository(conn)

    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=True,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    users = [
        UserContact(id="u1",
                    email="a@b.com",
                    phone=None,
                    is_verified=True,
                    notify_email=True,
                    notify_sms=False,
                    prefs=prefs)
    ]

    # First run sends
    run_poll_for_repo(repo_name=repo_name,
                      repo_label="New Grad",
                      poller=poller,
                      users=users,
                      sent_repo=sent_repo,
                      state_repo=state_repo,
                      notifier=notifier,
                      scraper=DummyScraper())
    assert len(sender.emails) == 1

    # Second run with same jobs should not send again due to DB dedupe
    run_poll_for_repo(repo_name=repo_name,
                      repo_label="New Grad",
                      poller=poller,
                      users=users,
                      sent_repo=sent_repo,
                      state_repo=state_repo,
                      notifier=notifier,
                      scraper=DummyScraper())
    assert len(sender.emails) == 1  # No additional email
