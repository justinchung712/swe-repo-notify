import os
from typing import Callable, List
from common.models import JobListing, UserContact


class NotificationService:
    """
    Batches and sends at most ONE email and/or ONE SMS per user per poll.
    `sender` must implement:
      - send_email(to_addr, subject, html_body, text_body)
      - send_sms(to_number, text_body)
    `edit_link_builder` is a function(user_contact) -> str
    """

    def __init__(self,
                 sender,
                 edit_link_builder: Callable[[UserContact], str],
                 unsubscribe_link_builder=None):
        self.sender = sender
        self.edit_link_builder = edit_link_builder
        self.unsubscribe_link_builder = unsubscribe_link_builder or (
            lambda u:
            f"{os.getenv('APP_BASE_URL','http://localhost:8000')}/request-edit-link"
        )

    def send_summary(self, user: UserContact, jobs: List[JobListing],
                     repo_label: str) -> None:
        # Guardrails
        if not user.is_verified:
            return
        if not jobs:
            return
        if not (user.notify_email or user.notify_sms):
            return

        # Build content
        edit_link = self.edit_link_builder(user)
        subject = self._subject(len(jobs), repo_label)
        ulink = self.unsubscribe_link_builder(user)
        text_body = self._text_body(jobs, edit_link, repo_label, ulink)
        html_body = self._html_body(jobs, edit_link, repo_label, ulink)

        # Channels
        if user.notify_email and user.email:
            self.sender.send_email(user.email, subject, html_body, text_body)
        if user.notify_sms and user.phone:
            # Keep SMS short; reuse text_body (built with brevity in mind)
            self.sender.send_sms(user.phone, text_body)

    @staticmethod
    def _subject(n: int, repo_label: str) -> str:
        return f"[{repo_label}] {n} new match{'es' if n != 1 else ''} for you"

    @staticmethod
    def _text_body(jobs: List[JobListing], edit_link: str, repo_label: str,
                   unsubscribe_link: str) -> str:
        # SMS-safe + email-compatible plain text
        lines = [
            f"{repo_label}: {len(jobs)} new match{'es' if len(jobs)!=1 else ''}"
        ]
        for j in jobs:
            # Single-line bullet per job
            loc = f" • {', '.join(j.locations)}" if j.locations else ""
            lines.append(f"- {j.title} @ {j.company_name}{loc} → {j.url}")
        lines.append("")
        lines.append(f"Edit your preferences: {edit_link}")
        lines.append(f"Unsubscribe: {unsubscribe_link}")
        lines.append("SMS: reply STOP to opt out.")
        return "\n".join(lines)

    @staticmethod
    def _html_body(jobs: List[JobListing], edit_link: str, repo_label: str,
                   unsubscribe_link: str) -> str:
        lis = []
        for j in jobs:
            loc = f" &middot; {', '.join(j.locations)}" if j.locations else ""
            lis.append(
                f"<li><a href='{j.url}'>{j.title}</a> @ {j.company_name}{loc}</li>"
            )
        return f"""
        <div>
          <p><strong>{repo_label}:</strong> {len(jobs)} new match{'es' if len(jobs)!=1 else ''}</p>
          <ul>
            {''.join(lis)}
          </ul>
          <p><a href="{edit_link}">Edit your preferences</a> · <a href="{unsubscribe_link}">Unsubscribe</a></p>
        </div>
        """.strip()
