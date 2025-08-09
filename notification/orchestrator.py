from typing import List, Dict, Any
from common.models import UserContact, JobListing, UserPreferences
from github_poller.matcher import MatchingEngine
from persistence.repositories import RepoStateRepository, SentNotificationsRepository
from notification.service import NotificationService

NEW_GRAD_REPO = "SimplifyJobs/New-Grad-Positions"
INTERNSHIP_REPO = "SimplifyJobs/Summer2026-Internships"  # Update if repo name changes


def _user_subscribed_to_repo(prefs: UserPreferences, repo_name: str) -> bool:
    if repo_name == NEW_GRAD_REPO:
        return bool(prefs.subscribe_new_grad)
    if repo_name == INTERNSHIP_REPO:
        return bool(prefs.subscribe_internship)
    # Default: unknown repo -> treat as not subscribed
    return False


def run_poll_for_repo(
    repo_name: str,
    repo_label: str,
    poller,  # Must have fetch_new_listings(since_sha) -> (List[JobListing], latest_sha)
    users: List[UserContact],
    sent_repo: SentNotificationsRepository,
    state_repo: RepoStateRepository,
    notifier: NotificationService,
) -> Dict[str, Any]:
    """
    Polls a single repo, matches jobs to users, sends at most ONE notification per user,
    dedupes via sent_notifications, and updates last_sha when done.
    Returns stats for logging/metrics.
    """
    last_sha = state_repo.get_last_sha(repo_name) or ""
    jobs, latest_sha = poller.fetch_new_listings(last_sha)

    users_notified = 0
    jobs_sent_total = 0
    jobs_considered = len(jobs)

    # For each user: filter by subscription, match, dedupe, batch send
    for user in users:
        if not user.is_verified:
            continue
        if not _user_subscribed_to_repo(user.prefs, repo_name):
            continue

        # Apply matching
        candidates = [j for j in jobs if MatchingEngine.matches(j, user.prefs)]

        # Idempotent dedupe: mark before send; only keep newly marked
        new_matches: List[JobListing] = []
        for j in candidates:
            if not sent_repo.was_sent(user.id, j.id):
                sent_repo.mark_sent(user.id, j.id)
                new_matches.append(j)

        if not new_matches:
            continue

        notifier.send_summary(user, new_matches, repo_label=repo_label)
        users_notified += 1
        jobs_sent_total += len(new_matches)

    # Advance SHA after processing; safe even if no users were notified
    if latest_sha and latest_sha != last_sha:
        state_repo.upsert_last_sha(repo_name, latest_sha)

    return {
        "repo_name": repo_name,
        "last_sha_before": last_sha,
        "last_sha_after": latest_sha or last_sha,
        "jobs_considered": jobs_considered,
        "users_notified": users_notified,
        "jobs_sent_total": jobs_sent_total,
    }
