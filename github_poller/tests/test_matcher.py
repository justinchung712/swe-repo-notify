import pytest
from common.models import JobListing, UserPreferences
from github_poller.matcher import MatchingEngine


@pytest.fixture
def sample_job():
    return JobListing(
        id="1",
        date_posted=0,
        url="u",
        company_name="C",
        title="Backend Engineer - Spring Boot & PostgreSQL",
        locations=["Remote"],
        sponsorship="None",
        active=True,
        source="Simplify",
    )


def test_receive_all_true_matches_any_job(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=True,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)


def test_role_keyword_matches_title(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=["backend"],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)


def test_tech_keyword_matches_title(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=["spring boot"],
                            role_keywords=[],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)


def test_location_keyword_matches_job(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=["remote"])
    assert MatchingEngine.matches(sample_job, prefs)


def test_no_keywords_matches_any_job(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)


def test_case_insensitive_matching(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=["POSTGRESQL"],
                            role_keywords=[],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)


def test_location_gate_blocks_non_matching_location(sample_job):
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=["spring boot"],
                            role_keywords=["backend"],
                            location_keywords=["new york"])
    assert not MatchingEngine.matches(sample_job, prefs)


def test_location_gate_passes_then_role_or_tech_can_match(sample_job):
    sample_job.locations = ["Chicago, IL"]
    sample_job.title = "Web Engineer"
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=["full stack", "engineer"],
                            location_keywords=["chicago"])
    assert MatchingEngine.matches(sample_job, prefs)


def test_location_gate_passes_then_role_or_tech_does_not_match(sample_job):
    sample_job.locations = ["Albany, NY"]
    sample_job.title = "Cybersecurity Engineer"
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=["backend"],
                            location_keywords=["albany"])
    assert not MatchingEngine.matches(sample_job, prefs)


def test_location_gate_with_no_role_tech_means_any_job_in_locations(
        sample_job):
    sample_job.locations = ["Toronto, Canada"]
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=[],
                            role_keywords=[],
                            location_keywords=["canada"])
    assert MatchingEngine.matches(sample_job, prefs)


def test_tech_keyword_matches_description(sample_job):
    sample_job.title = "Engineer"
    sample_job.description = "We use Rust, Kafka, and Kubernetes."
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=["kubernetes"],
                            role_keywords=[],
                            location_keywords=[])
    assert MatchingEngine.matches(sample_job, prefs)
