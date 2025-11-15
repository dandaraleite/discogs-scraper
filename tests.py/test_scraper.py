from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import NoSuchElementException

from rock_genre.constants import BASE_URL, GENRE
from rock_genre.scraper import get_artist_data, get_artists_by_genre


@pytest.fixture
def mock_driver():
    """Creates a mock for the WebDriver."""
    return MagicMock()


@pytest.fixture
def mock_link_element():
    """Creates a mock for an 'a' element with get_attribute and .text property."""

    def _mock_link(href_value, text_value=""):
        mock_a = MagicMock()
        mock_a.get_attribute.return_value = href_value
        type(mock_a).text = property(lambda self: text_value)
        return mock_a

    return _mock_link


@pytest.fixture(autouse=True)
def mock_safe_text(monkeypatch):
    """Mocks safe_text to return the text directly from the element mock."""

    def mock_st(elem):
        return elem.text.strip() if hasattr(elem, "text") and elem.text else ""

    monkeypatch.setattr("rock_genre.scraper.safe_text", mock_st)


@patch("rock_genre.scraper.WebDriverWait", MagicMock())
@patch("rock_genre.scraper.handle_language_warning", MagicMock())
@patch("rock_genre.scraper.random_delay", MagicMock())
def test_get_artists_by_genre_collects_and_deduplicates(mock_driver, mock_link_element):
    """Tests URL collection from multiple lists, deduplication, and limits."""

    mock_list_1 = MagicMock()
    mock_list_1.find_elements.return_value = [
        mock_link_element(f"{BASE_URL}/artist/1-A?query=x"),
        mock_link_element(f"{BASE_URL}/artist/2-B"),
        mock_link_element(f"{BASE_URL}/artist/1-A"),
        mock_link_element("https://other.com/link"),
    ]

    mock_list_2 = MagicMock()
    mock_list_2.find_elements.return_value = [
        mock_link_element(f"{BASE_URL}/artist/3-C"),
        mock_link_element(f"{BASE_URL}/artist/2-B"),
    ]

    mock_driver.find_element.side_effect = [
        MagicMock(),
        mock_list_1,
        mock_list_2,
        NoSuchElementException,
        NoSuchElementException,
    ]

    result = get_artists_by_genre(mock_driver, "rock", limit=10)

    expected_urls = [
        f"{BASE_URL}/artist/1-A",
        f"{BASE_URL}/artist/2-B",
        f"{BASE_URL}/artist/3-C",
    ]

    assert len(result) == 3
    assert result == expected_urls


@patch("rock_genre.scraper.WebDriverWait", MagicMock())
@patch("rock_genre.scraper.handle_language_warning", MagicMock())
@patch("rock_genre.scraper.random_delay", MagicMock())
def test_get_artists_by_genre_respects_limit(mock_driver, mock_link_element):
    """Tests if collection stops when the limit is reached."""

    mock_list_1 = MagicMock()
    mock_list_1.find_elements.return_value = [
        mock_link_element(f"{BASE_URL}/artist/1"),
        mock_link_element(f"{BASE_URL}/artist/2"),
    ]
    mock_list_2 = MagicMock()
    mock_list_2.find_elements.return_value = [
        mock_link_element(f"{BASE_URL}/artist/3"),
        mock_link_element(f"{BASE_URL}/artist/4"),
    ]

    mock_driver.find_element.side_effect = [
        MagicMock(),
        mock_list_1,
        mock_list_2,
        NoSuchElementException,
        NoSuchElementException,
    ]

    result = get_artists_by_genre(mock_driver, "rock", limit=3)

    assert len(result) == 3
    assert f"{BASE_URL}/artist/4" not in result


@patch("rock_genre.scraper.get_album_data", MagicMock(return_value={"id": "album"}))
@patch("rock_genre.scraper.WebDriverWait", MagicMock())
@patch("rock_genre.scraper.handle_language_warning", MagicMock())
@patch("rock_genre.scraper.random_delay", MagicMock())
def test_get_artist_data_members_websites_albums(mock_driver, mock_link_element):
    """Tests extraction of name, members, websites, and album limits."""

    mock_h1 = MagicMock(text="The Test Band")
    mock_member_link = mock_link_element("/artist/member", "Member A")
    mock_website_link = mock_link_element("https://test.com/site", "site")

    mock_album_links = [
        mock_link_element("/release/100"),
        mock_link_element("/master/200"),
        mock_link_element("/release/300"),
        mock_link_element("/release/400"),
    ]

    # find_elements sequence: 1. Members; 2. Websites; 3. Albums.
    mock_driver.find_elements.side_effect = [
        [mock_member_link],
        [mock_website_link],
        mock_album_links,
    ]

    mock_driver.find_element.return_value = mock_h1

    result = get_artist_data(mock_driver, "url", GENRE, album_limit=2)

    assert result["artist_name"] == "The Test Band"
    assert result["members"] == ["Member A"]
    assert result["websites"] == ["https://test.com/site"]
    assert len(result["albums"]) == 2
