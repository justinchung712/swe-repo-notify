import os
from persistence.db import get_conn, init_db
from persistence.repositories import RepoStateRepository, SentNotificationsRepository, UserRepository
from notification.service import NotificationService
from notification.orchestrator import run_poll_for_repo, NEW_GRAD_REPO, INTERNSHIP_REPO
from notification.users import hydrate_users
from job_scraper.scraper import JobScraper
from github_poller.poller import GithubPoller


def get_github_token():
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        return token
    try:
        import subprocess
        return subprocess.check_output(["gh", "auth",
                                        "token"]).decode().strip()
    except Exception:
        return None


class ConsoleSender:

    def send_email(self, to_addr, subject, html_body, text_body):
        print(f"[EMAIL → {to_addr}] {subject}\n{text_body}\n")

    def send_sms(self, to_number, text_body):
        print(f"[SMS → {to_number}] {text_body}\n")


def build_edit_link(user_contact):
    base = os.getenv("APP_BASE_URL", "http://localhost:8000")
    return f"{base}/request-edit-link"  # MVP: message points them to request a fresh link


def main():
    conn = get_conn(os.getenv("DB_PATH") or "db.sqlite3")
    init_db(conn)
    user_repo = UserRepository(conn)
    state_repo = RepoStateRepository(conn)
    sent_repo = SentNotificationsRepository(conn)

    rows = user_repo.list_verified_users()
    users = hydrate_users(rows)

    sender = ConsoleSender()  # Swap to real providers later
    notifier = NotificationService(sender, edit_link_builder=build_edit_link)
    scraper = JobScraper(cache=None, use_headless_fallback=False)

    token = get_github_token() or ""

    ng = GithubPoller("SimplifyJobs", "New-Grad-Positions", token=token)
    internships = GithubPoller("SimplifyJobs",
                               "Summer2026-Internships",
                               token=token)

    stats1 = run_poll_for_repo(repo_name=NEW_GRAD_REPO,
                               repo_label="New Grad",
                               poller=ng,
                               users=users,
                               sent_repo=sent_repo,
                               state_repo=state_repo,
                               notifier=notifier,
                               scraper=scraper)
    print("NG stats:", stats1)

    stats2 = run_poll_for_repo(repo_name=INTERNSHIP_REPO,
                               repo_label="Internships",
                               poller=internships,
                               users=users,
                               sent_repo=sent_repo,
                               state_repo=state_repo,
                               notifier=notifier,
                               scraper=scraper)
    print("Intern stats:", stats2)


if __name__ == "__main__":
    main()
