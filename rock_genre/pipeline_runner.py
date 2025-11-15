import jsonlines

from rock_genre.constants import (
    ALBUM_LIMIT,
    ARTIST_LIMIT,
    BASE_URL,
    GENRE,
    GENRE_SLUG,
    OUTPUT_FILE,
    WAIT_TIMEOUT,
)
from rock_genre.helpers import init_driver, random_delay, reject_cookies
from rock_genre.scraper import get_artist_data, get_artists_by_genre


def process_artists_and_save(driver, artists: list, genre: str, album_limit: int):
    """Iterates over the artists, collects data, and saves it to a JSONL file.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.
    artists : List[str]
        A list of Discogs artist URLs to scrape.
    genre : str
        The music genre associated with the artists (used for the output filename).
    album_limit : int
        The maximum number of albums to scrape for each artist.

    Returns
    -------
    None
        This function does not return a value.
    """
    all_artists = []

    for idx, artist_url in enumerate(artists, start=1):
        print(f"[INFO] ({idx}/{len(artists)}) Processing artist data: {artist_url}")

        # Chama a função de extração de dados do artista
        artist_data = get_artist_data(driver, artist_url, genre, album_limit)

        if artist_data:
            all_artists.append(artist_data)
        else:
            print(f"[WARN] Failed to extract artist data: {artist_url}")

        # Delay between artists to avoid blockade.
        random_delay()

    # Salvar JSONL
    with jsonlines.open(OUTPUT_FILE, mode="w") as writer:
        for artist in all_artists:
            writer.write(artist)

    print(f"[DONE] Salved {len(all_artists)} artists in {OUTPUT_FILE}")
    return len(all_artists)


def main(artist_limit=ARTIST_LIMIT, album_limit=ALBUM_LIMIT, headless=True):
    """Executes the main scraping workflow to collect artist and album data.

    Initializes the Selenium WebDriver, navigates to the genre page, collects
    artist links, and processes the data, saving the results to a file.

    Parameters
    ----------
    artist_limit : int, optional
        The maximum number of artists to scrape from the genre page,
        defaults to ARTIST_LIMIT from constants.
    album_limit : int, optional
        The maximum number of albums to scrape for each artist,
        defaults to ALBUM_LIMIT from constants.
    headless : bool, optional
        If True, runs the WebDriver in headless mode (no visible browser UI),
        defaults to True.

    Returns
    -------
    None
        This function does not return a value.
    """
    # Inicialization and navigation
    driver = init_driver(headless=headless)

    genre_url = f"{BASE_URL}/genre/{GENRE_SLUG}"
    try:
        driver.get(genre_url)
        reject_cookies(driver, wait_timeout=WAIT_TIMEOUT)

        artists = get_artists_by_genre(driver, GENRE_SLUG, artist_limit)
        print(f"[INFO] Found {len(artists)} artists (limit requested {artist_limit})")

        if not artists:
            print("[WARN] No valid artist URL found. Closing.")
            return

        process_artists_and_save(driver, artists, GENRE, album_limit)

    except Exception as e:
        print(f"[FATAL] An unexpected error occurred during execution: {e}")

    finally:
        driver.quit()
        print("[INFO] Selenium driver closed.")


if __name__ == "__main__":
    main(artist_limit=ARTIST_LIMIT, album_limit=ALBUM_LIMIT, headless=True)
