import re
import uuid

from selenium.common.exceptions import (
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from rock_genre.constants import (
    BASE_URL,
    WAIT_TIMEOUT,
)
from rock_genre.helpers import handle_language_warning, random_delay, safe_text


def get_artists_by_genre(driver, genre_slug: str, limit: int) -> list[str]:
    """
    Retrieves a list of unique artist URLs from all relevant sections
    (Most Collected, Top Artists, etc.) on the genre page.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.
    genre_slug : str
        The URL slug for the genre (e.g., 'rock').
    limit : int
        The maximum number of unique artist URLs to collect.

    Returns
    -------
    list[str]
        A list of normalized, unique Discogs artist URLs.
    """
    url = f"{BASE_URL}/genre/{genre_slug}"
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    print("[INFO] Loading the genre page...")

    LIST_SELECTORS = [
        "ul#most_collected",
        "ul#top_artists",
        "ul#early_masters",
        "ul#top_mp_items",
    ]

    ARTIST_LINK_SELECTOR = "a[href*='/artist/']"

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LIST_SELECTORS[0])))
        print("[INFO] Main content sections loaded.")
    except Exception:
        print(f"Failed to find the main releases section in {WAIT_TIMEOUT}s.")
        return []

    # 2. Collection: Iterates over ALL selectors and collects artist links for each one.
    seen_paths = set()
    artists = []

    for selector in LIST_SELECTORS:
        if len(artists) >= limit:
            break

        try:
            current_list = driver.find_element(By.CSS_SELECTOR, selector)

            possible_artists = current_list.find_elements(
                By.CSS_SELECTOR, ARTIST_LINK_SELECTOR
            )

            for a in possible_artists:
                href = a.get_attribute("href")

                # Ensures the link is valid and points to an artist.
                if not href or "/artist/" not in href:
                    continue

                # Normalization and Deduplication
                normalized_path = href.split("?")[0].split(BASE_URL)[-1].strip()
                full_url = f"{BASE_URL}{normalized_path}"

                if normalized_path not in seen_paths:
                    seen_paths.add(normalized_path)
                    artists.append(full_url)

                # Check the limit after each addition.
                if len(artists) >= limit:
                    break

        except NoSuchElementException:
            # If the list (ul) for this selector is not found, ignore it and try the next one.
            continue
        except Exception as e:
            print(f"[WARN] Error collecting artists from the selector {selector}: {e}")
            continue

    print(f"[DEBUG] Found {len(artists)} unique artists.")
    print(f"{len(artists)} artist(s) found (limit requested) {limit}):")
    for r in artists:
        print("  -", r)

    return artists


def get_artist_data(
    driver, artist_url: str, genre: str, album_limit: int
) -> dict | None:
    """
    Extracts artist metadata (name, members, websites) and collects data
    for up to `album_limit` albums by calling `get_album_data`.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.
    artist_url : str
        The URL of the artist's Discogs page.
    genre : str
        The genre associated with the artist.
    album_limit : int
        The maximum number of albums to scrape for this artist.

    Returns
    -------
    Optional[dict]
        A dictionary containing the artist's structured data, or None if the
        artist page fails to load or the title cannot be extracted.
    """
    try:
        driver.get(artist_url)
    except Exception:
        return None

    handle_language_warning(driver)

    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except Exception:
        print(f"[WARN] Timeout while loading artist h1 in{WAIT_TIMEOUT}s: {artist_url}")
        return None

    random_delay()

    # Artist name
    try:
        artist_name = safe_text(driver.find_element(By.TAG_NAME, "h1"))
    except Exception:
        artist_name = None

    # Members
    members = []
    try:
        # Busca a célula de dados (td) que segue o cabeçalho (th) que contém 'Members' ou 'Membros'
        member_links = driver.find_elements(
            By.XPATH,
            "//th[contains(., 'Members') or contains(., 'Membros')]/following-sibling::td[1]//a[contains(@href, '/artist/')]",
        )

        for a in member_links:
            t = safe_text(a)
            if t:
                members.append(t)
        # Simple deduplication
        members = list(set(members))

    except Exception:
        # print(f"[DEBUG] Falha ao extrair membros: {e}")
        members = []

    # Websites
    websites = []
    try:
        sites = driver.find_elements(
            By.XPATH,
            "//th[h2[text()='Sites' or text()='Websites']]/following-sibling::td//a",
        )

        for a in sites:
            href = a.get_attribute("href")

            # Ensure the link is not empty and is unique.
            if href and href not in websites:
                websites.append(href)
    except Exception as e:
        print(f"[WARN] Failed to extract websites: {e}")
        websites = []

    # Releases/Albums: Collection, Deduplication and Limitation
    album_links = []
    try:
        candidate_links = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/release/'], a[href*='/master/']"
        )

        # Dedupe and limit in a single pass.
        seen = set()
        for a in candidate_links:
            href = a.get_attribute("href")
            if href and ("/release/" in href or "/master/" in href):
                normalized_url = href.split("?")[0]
                if normalized_url not in seen:
                    seen.add(normalized_url)
                    album_links.append(normalized_url)
                    if len(album_links) >= album_limit:
                        break  # Sai do loop de coleta de links

    except Exception:
        album_links = []

    # Collect Album Data
    albums = []
    for a_url in album_links:
        album_data = get_album_data(driver, a_url)
        if album_data:
            # Não é necessário checar duplicação por nome de álbum aqui,
            # pois já checamos duplicação de URL na etapa anterior.
            albums.append(album_data)
        random_delay()

    artist_obj = {
        "artist_id": str(uuid.uuid4()),
        "genre": genre,
        "artist_name": artist_name,
        "members": members,
        "websites": websites,
        "albums": albums,
        "source_url": artist_url,
    }
    return artist_obj


def get_album_data(driver, album_url: str) -> dict | None:
    """
    Extracts album metadata (name, year, label, styles) and tracklist
    data using robust XPath and CSS heuristics.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.
    album_url : str
        The URL of the album's Discogs page.

    Returns
    -------
    Optional[dict]
        A dictionary containing the album's structured data, or None if the
        album page fails to load.
    """
    try:
        driver.get(album_url)
    except Exception:
        return None

    # Page Initialization
    handle_language_warning(driver)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    try:
        # Wait for the H1 (title) to appear.
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except Exception:  # noqa: S110
        # Allows the script to continue extracting even if the H1 doesn't load in time.
        pass
    random_delay()

    page_html = driver.page_source

    # METADADOS:
    # Nome do Álbum (H1)
    album_name = (
        safe_text(driver.find_element(By.TAG_NAME, "h1"))
        if driver.find_elements(By.TAG_NAME, "h1")
        else None
    )
    album_name_raw = album_name  # Usado para filtrar ruído nas faixas

    # Release Year
    release_year = None
    try:
        year_elem = driver.find_element(
            By.XPATH,
            "//th[contains(., 'Year') or contains(., 'Ano')]/following-sibling::td[1]//a",
        )
        href = year_elem.get_attribute("href")
        year_match = re.search(r"year=(\d{4})", href)
        release_year = year_match.group(1) if year_match else safe_text(year_elem)
    except Exception:
        # Fallback RegEx
        years = re.findall(r"\b(19|20)\d{2}\b", page_html)
        if years:
            release_year = years[0]

    # 2. Label
    label = None
    try:
        label_elem = driver.find_element(By.CSS_SELECTOR, "a[href*='/label/']")
        label = safe_text(label_elem)
    except Exception:
        try:
            # fallback XPath selector
            label_elems = driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'Label') or contains(text(),'Gravadora')]/following-sibling::*//a",
            )
            if label_elems:
                label = safe_text(label_elems[0])
        except Exception:  # noqa: S110
            pass

    # Styles
    styles = []
    try:
        style_td = driver.find_element(
            By.XPATH,
            "//th[h2[contains(., 'Style') or contains(., 'Estilo')]]/following-sibling::td[1]",
        )
        style_anchors = style_td.find_elements(By.TAG_NAME, "a")

        for s in style_anchors:
            txt = safe_text(s)
            # Filtro básico de comprimento e duplicidade
            if 2 < len(txt) < 30 and txt not in styles:
                styles.append(txt)
    except Exception as e:
        print(f"[WARN] Failed to extract styles by XPath: {e}")
        styles = []

    # TRACKS: EXTRACT
    tracks = []

    # XPath for TR lines containing a TD with duration (via class or MM:SS heuristic format)
    TRACK_ROW_XPATH = (
        "//table[contains(@class, 'tracklist_')]//tr["
        ".//td[contains(@class, 'duration_') or (contains(text(), ':') and string-length(normalize-space()) < 7)]]"
    )
    # XPath Finder for the DURATION element within the line (TR)
    DUR_ELEMENT_FINDER = ".//*[contains(@class, 'duration_') or (contains(text(), ':') and string-length(normalize-space()) < 7)]"

    try:
        rows = driver.find_elements(By.XPATH, TRACK_ROW_XPATH)
        tn = 1
        for r in rows:
            name, dur_raw = None, None

            # Duration
            try:
                dur_elem = r.find_element(By.XPATH, DUR_ELEMENT_FINDER)
                dur_raw = safe_text(dur_elem)
            except NoSuchElementException:
                pass  # It's not fatal if the duration fails.

            # Track Name
            try:
                # Prioritizes the span with the title class.
                name = safe_text(
                    r.find_element(By.CSS_SELECTOR, "span[class*='tracklistTitle']")
                )
            except NoSuchElementException:
                # Fallback: search for the longest text that is not the duration.
                all_texts = r.find_elements(By.XPATH, ".//td/span | .//td/a")
                for t in all_texts:
                    ttxt = safe_text(t)
                    if ttxt and ttxt != dur_raw and len(ttxt) > 5:
                        name = ttxt
                        break

            # INTEGRITY FILTERS: If the name fails, skip to the next one (continue)
            if (
                not name
                or re.match(r"^\d+$", name)
                or (
                    album_name_raw
                    and album_name_raw in name
                    and len(name) < len(album_name_raw) + 10
                )
            ):
                continue

            # Add the track
            tracks.append(
                {
                    "track_number": tn,
                    "track_name": name,
                    "duration": dur_raw,
                }
            )
            tn += 1

    except Exception as e:
        print(f"[DEBUG] Failed to extract tracklist via XPath: {e}")
        tracks = []

    # Sort by track_number (only one guardrail)
    tracks = sorted(tracks, key=lambda t: t.get("track_number", 9999))

    # Final Return
    album_obj = {
        "album_id": str(uuid.uuid4()),
        "album_name": album_name,
        "release_year": release_year,
        "label": label,
        "styles": styles,
        "tracks": tracks,
        "source_url": album_url,
    }
    return album_obj
