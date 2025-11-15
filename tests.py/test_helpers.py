from unittest.mock import MagicMock

import pytest

from rock_genre.constants import DELAY_MAX, DELAY_MIN
from rock_genre.helpers import (
    handle_language_warning,
    random_delay,
    reject_cookies,
    safe_text,
)


def test_safe_text_success():
    mock_elem = MagicMock()
    mock_elem.text = "   Clean Text "
    assert safe_text(mock_elem) == "Clean Text"


def test_random_delay_calls_sleep_and_random(monkeypatch):
    mock_sleep = MagicMock()
    mock_uniform = MagicMock(return_value=DELAY_MIN)

    monkeypatch.setattr("time.sleep", mock_sleep)
    monkeypatch.setattr("random.uniform", mock_uniform)

    random_delay()

    # Checks if random.uniform was called with the defined limits
    mock_uniform.assert_called_once_with(DELAY_MIN, DELAY_MAX)
    # Checks if time.sleep was called with the value returned by mock_uniform
    mock_sleep.assert_called_once_with(DELAY_MIN)


# We create a fixture to mock the wait (WebDriverWait) in all pop-up functions
@pytest.fixture
def mock_wait_until(monkeypatch):
    """Fixture that replaces the entire WebDriverWait class."""

    # Creates the mock for the until method, which will be called inside the function
    mock_until_method = MagicMock()

    # 1. Creates the WebDriverWait Mock class
    mock_wait_class = MagicMock()
    # 2. Ensures that any instance of this class (new WebDriverWait(...))
    #    will have its .until() method mocked.
    mock_wait_class.return_value.until = mock_until_method

    # Replaces the actual class in the helpers module
    monkeypatch.setattr("rock_genre.helpers.WebDriverWait", mock_wait_class)

    # Mocks random_delay as well
    monkeypatch.setattr("rock_genre.helpers.random_delay", MagicMock())

    # Returns the mock of the .until method so tests can configure the side_effect
    return mock_until_method


def test_reject_cookies_reject_success(mock_wait_until):
    mock_reject_button = MagicMock()

    # Configures the first call to until() (Reject) to return the button
    mock_wait_until.return_value = mock_reject_button

    result = reject_cookies(MagicMock())

    mock_reject_button.click.assert_called_once()
    assert result is True


def test_reject_cookies_fallback_accept(mock_wait_until):
    mock_accept_button = MagicMock()

    # Configures until() to fail on the first call (Reject) and return the button on the second (Accept)
    mock_wait_until.side_effect = [
        Exception("Simulating Reject failure"),
        mock_accept_button,
    ]

    result = reject_cookies(MagicMock())

    mock_accept_button.click.assert_called_once()
    assert result is True


def test_reject_cookies_total_failure(mock_wait_until):
    # Configures until() to fail on both calls
    mock_wait_until.side_effect = Exception("Total failure")

    result = reject_cookies(MagicMock())

    assert result is False


def test_handle_language_warning_success(mock_wait_until):
    """Tests the successful click on the language warning and waiting for H1."""
    mock_driver = MagicMock()
    mock_link = MagicMock()

    # Configures the side_effect of the .until() method (which is what the fixture returns)
    mock_wait_until.side_effect = [
        mock_link,  # 1st call: Find and click the link. Returns the link.
        True,  # 2nd call: Wait for H1 after the click. Returns success (True).
    ]

    result = handle_language_warning(mock_driver)

    mock_link.click.assert_called_once()
    assert result is True


def test_handle_language_warning_failure(mock_wait_until):
    mock_wait_until.side_effect = Exception("Timeout")

    result = handle_language_warning(MagicMock())

    assert result is False
