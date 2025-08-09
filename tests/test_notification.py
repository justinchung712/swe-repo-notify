import pytest
from common.models import UserPreferences, JobListing, UserContact
from notification.service import NotificationService


class FakeSender:

    def __init__(self):
        self.emails = []
        self.sms = []

    def send_email(self, to_addr: str, subject: str, html_body: str,
                   text_body: str):
        self.emails.append((to_addr, subject, html_body, text_body))

    def send_sms(self, to_number: str, text_body: str):
        self.sms.append((to_number, text_body))


def sample_job(i=1,
               title="Software Engineer",
               company="Acme",
               url="https://ex.com"):
    return JobListing(
        id=str(i),
        date_posted=0,
        url=url,
        company_name=company,
        title=title,
        locations=["Remote"],
        sponsorship="None",
        active=True,
        source="Simplify",
    )


@pytest.fixture
def prefs_all():
    return UserPreferences(subscribe_new_grad=True,
                           subscribe_internship=False,
                           receive_all=True,
                           tech_keywords=[],
                           role_keywords=[],
                           location_keywords=[])


def test_send_summary_email_only(prefs_all):
    user = UserContact(id="u1",
                       email="a@b.com",
                       phone=None,
                       is_verified=True,
                       notify_email=True,
                       notify_sms=False,
                       prefs=prefs_all)
    jobs = [
        sample_job(1, "Backend Engineer", "Foo", "u1"),
        sample_job(2, "DevOps Engineer", "Bar", "u2")
    ]
    sender = FakeSender()
    svc = NotificationService(sender,
                              edit_link_builder=lambda u: "https://edit/link")
    svc.send_summary(user, jobs, repo_label="New Grad")

    assert len(sender.emails) == 1
    to, subject, html, text = sender.emails[0]
    assert to == "a@b.com"
    assert "2 new matches" in subject.lower()
    assert "Backend Engineer" in text and "DevOps Engineer" in text
    assert "edit your preferences" in text.lower()

    assert len(sender.sms) == 0


def test_send_summary_sms_only(prefs_all):
    user = UserContact(id="u1",
                       email=None,
                       phone="+15551234567",
                       is_verified=True,
                       notify_email=False,
                       notify_sms=True,
                       prefs=prefs_all)
    jobs = [sample_job(1, "QA Engineer", "Baz", "u3")]
    sender = FakeSender()
    svc = NotificationService(sender,
                              edit_link_builder=lambda u: "https://edit/link")
    svc.send_summary(user, jobs, repo_label="Internships")

    assert len(sender.sms) == 1
    num, text = sender.sms[0]
    assert num == "+15551234567"
    assert "1 new match" in text.lower()
    assert "QA Engineer" in text


def test_unverified_user_sends_nothing(prefs_all):
    user = UserContact(id="u1",
                       email="x@x.com",
                       phone="+1",
                       is_verified=False,
                       notify_email=True,
                       notify_sms=True,
                       prefs=prefs_all)
    jobs = [sample_job(1)]
    sender = FakeSender()
    svc = NotificationService(sender,
                              edit_link_builder=lambda u: "https://edit/link")
    svc.send_summary(user, jobs, repo_label="New Grad")

    assert sender.emails == []
    assert sender.sms == []


def test_no_channels_enabled_sends_nothing(prefs_all):
    user = UserContact(id="u1",
                       email="x@x.com",
                       phone="+1",
                       is_verified=True,
                       notify_email=False,
                       notify_sms=False,
                       prefs=prefs_all)
    jobs = [sample_job(1)]
    sender = FakeSender()
    svc = NotificationService(sender,
                              edit_link_builder=lambda u: "https://edit/link")
    svc.send_summary(user, jobs, repo_label="New Grad")
    assert sender.emails == []
    assert sender.sms == []


def test_empty_job_list_sends_nothing(prefs_all):
    user = UserContact(id="u1",
                       email="x@x.com",
                       phone="+1",
                       is_verified=True,
                       notify_email=True,
                       notify_sms=True,
                       prefs=prefs_all)
    sender = FakeSender()
    svc = NotificationService(sender,
                              edit_link_builder=lambda u: "https://edit/link")
    svc.send_summary(user, [], repo_label="New Grad")
    assert sender.emails == []
    assert sender.sms == []
