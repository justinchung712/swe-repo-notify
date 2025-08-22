import os
import socket
import uuid

from persistence.db import get_conn, init_db
from persistence.repositories import RepoStateRepository, SentNotificationsRepository, UserRepository
from persistence.lock import acquire_lock
from notification.service import NotificationService
from notification.orchestrator import run_poll_for_repo, NEW_GRAD_REPO, INTERNSHIP_REPO
from notification.users import hydrate_users
from job_scraper.scraper import JobScraper
from github_poller.poller import GithubPoller
from api.security import make_token
from common.models import UserContact


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


def build_edit_link(user: UserContact) -> str:
    base = os.getenv("APP_BASE_URL", "http://localhost:8000")
    token = make_token({"purpose": "edit", "uid": user.id})
    return f"{base}/edit?token={token}"


def build_unsubscribe_link(user: UserContact) -> str:
    base = os.getenv("APP_BASE_URL", "http://localhost:8000")
    token = make_token({"purpose": "unsubscribe", "uid": user.id})
    return f"{base}/unsubscribe?token={token}"


def main():
    conn = get_conn(os.getenv("DB_PATH") or "db.sqlite3")
    init_db(conn)
    user_repo = UserRepository(conn)
    state_repo = RepoStateRepository(conn)
    sent_repo = SentNotificationsRepository(conn)

    rows = user_repo.list_verified_users()
    users = hydrate_users(rows)

    sender = ConsoleSender()
    notifier = NotificationService(
        sender,
        edit_link_builder=build_edit_link,
        unsubscribe_link_builder=build_unsubscribe_link)
    scraper = JobScraper(cache=None, use_headless_fallback=False)

    token = get_github_token() or ""

    NG_BRANCH = os.getenv("NG_BRANCH", "dev")
    INTERN_BRANCH = os.getenv("INTERN_BRANCH", "dev")

    ng = GithubPoller("SimplifyJobs",
                      "New-Grad-Positions",
                      token=token,
                      branch=NG_BRANCH)
    internships = GithubPoller("SimplifyJobs",
                               "Summer2026-Internships",
                               token=token,
                               branch=INTERN_BRANCH)

    locker_owner = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"

    # Run each repo under its own lock to avoid double-processing
    for label, repo_name, poller in [
        ("NG", NEW_GRAD_REPO, ng),
        ("Intern", INTERNSHIP_REPO, internships),
    ]:
        lock_name = f"poller:{repo_name}"
        # Hold the lock up to 120s; skip if unable to get it quickly
        from_time = "start"
        with acquire_lock(conn,
                          name=lock_name,
                          owner=locker_owner,
                          ttl_seconds=120) as ok:
            if not ok:
                print(f"[{label}] Another instance holds the lock; skipping.")
                continue

            stats = run_poll_for_repo(
                repo_name=repo_name,
                repo_label="New Grad" if label == "NG" else "Internships",
                poller=poller,
                users=users,
                sent_repo=sent_repo,
                state_repo=state_repo,
                notifier=notifier,
                scraper=scraper,
            )
            print(f"[{label}] stats:", stats)


if __name__ == "__main__":
    import signal, sys, traceback

    def _timeout_handler(signum, frame):
        print("[POLL_ONCE] Global 10m timeout; exiting gracefully.")
        sys.exit(0)

    # Guard the whole run to prevent overlapping cron invocations
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(10 * 60)

    try:
        main()
    except Exception:
        print("[POLL_ONCE] Unhandled error:", file=sys.stderr)
        traceback.print_exc()
        # Exit 0 so supercronic doesn't keep reporting exit status 1 repeatedly
        sys.exit(0)
    finally:
        signal.alarm(0)
