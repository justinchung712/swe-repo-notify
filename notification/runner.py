from typing import Dict, Any, List
from persistence.repositories import (RepoStateRepository,
                                      SentNotificationsRepository,
                                      UserRepository)
from notification.service import NotificationService
from notification.orchestrator import (run_poll_for_repo, NEW_GRAD_REPO,
                                       INTERNSHIP_REPO)
from notification.users import hydrate_users
from job_scraper.scraper import JobScraper
from github_poller.poller import GithubPoller


def run_all_repos_once(
    user_repo: UserRepository,
    state_repo: RepoStateRepository,
    sent_repo: SentNotificationsRepository,
    notifier: NotificationService,
    scraper: JobScraper,
    github_token: str = "",
) -> Dict[str, Any]:
    """Run both repos once. Returns a dict of stats by repo_name."""
    rows = user_repo.list_verified_users()
    users = hydrate_users(rows)

    ng_poller = GithubPoller("SimplifyJobs",
                             "New-Grad-Positions",
                             token=github_token)
    intern_poller = GithubPoller("SimplifyJobs",
                                 "Summer2026-Internships",
                                 token=github_token)

    stats = {}
    stats[NEW_GRAD_REPO] = run_poll_for_repo(repo_name=NEW_GRAD_REPO,
                                             repo_label="New Grad",
                                             poller=ng_poller,
                                             users=users,
                                             sent_repo=sent_repo,
                                             state_repo=state_repo,
                                             notifier=notifier,
                                             scraper=scraper)
    stats[INTERNSHIP_REPO] = run_poll_for_repo(repo_name=INTERNSHIP_REPO,
                                               repo_label="Internships",
                                               poller=intern_poller,
                                               users=users,
                                               sent_repo=sent_repo,
                                               state_repo=state_repo,
                                               notifier=notifier,
                                               scraper=scraper)
    return stats
