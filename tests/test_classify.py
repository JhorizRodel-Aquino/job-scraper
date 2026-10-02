import pytest

from job_scraper.classify import classify_sub_role, is_philippines, is_relevant


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Senior Software Engineer", True),
        ("Backend Developer", True),
        ("SDE II, Payments", True),
        ("Marketing Manager", False),
        ("Sales Development Representative", False),
        ("Warehouse Associate", False),
    ],
)
def test_is_relevant(title: str, expected: bool) -> None:
    assert is_relevant(title) is expected


@pytest.mark.parametrize(
    "title,expected_role",
    [
        ("Senior Backend Engineer", "backend"),
        ("Frontend Developer (React)", "frontend"),
        ("Full Stack Software Engineer", "full-stack"),
        ("DevOps Engineer", "devops"),
        ("Site Reliability Engineer", "devops"),
        ("iOS Developer", "mobile"),
        ("Android Software Engineer", "mobile"),
        ("Software Engineer, Payments Platform", "other"),
    ],
)
def test_classify_sub_role(title: str, expected_role: str) -> None:
    assert classify_sub_role(title) == expected_role


def test_devops_wins_over_backend_when_both_present() -> None:
    # "Backend DevOps Engineer" contains both, devops keywords are checked first.
    assert classify_sub_role("Backend DevOps Engineer") == "devops"


@pytest.mark.parametrize(
    "location,expected",
    [
        ("Manila, Philippines", True),
        ("Remote in the Philippines", True),
        ("Clark, Pampanga", True),  # city/province with no literal "Philippines"
        ("Makati City, Metro Manila", True),
        ("Remote - Malaysia; Remote - Philippines", True),
        ("Austin, TX", False),
        (None, False),
        ("", False),
    ],
)
def test_is_philippines(location: str | None, expected: bool) -> None:
    assert is_philippines(location) is expected
