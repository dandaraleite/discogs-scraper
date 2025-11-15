import random
import time

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from rock_genre.constants import DELAY_MAX, DELAY_MIN

WebDriver = webdriver.Chrome


def init_driver(headless: bool = True):
    """Initializes and configures the Selenium WebDriver (Chrome).

    Sets up necessary options, including running in headless mode (if enabled)
    and adding arguments to prevent automation detection.

    Parameters
    ----------
    headless : bool, optional
        If True, runs the browser without a visible UI, defaults to True.

    Returns
    -------
    WebDriver
        The configured Chrome WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # avoids detecting automation in some cases.
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.set_window_size(1200, 900)
    return driver


def random_delay() -> None:
    """Pauses execution for a random duration within defined limits.

    The pause duration is uniformly distributed between DELAY_MIN and DELAY_MAX
    (from constants.py).

    Returns
    -------
    None
        This function does not return a value.
    """
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # noqa: S311


def safe_text(elem) -> str:
    """Safely extracts and strips the text content from a WebElement.

    Handles common exceptions that occur when the element is missing or stale.

    Parameters
    ----------
    elem : WebElement
        The WebElement from which to extract text.

    Returns
    -------
    str
        The stripped text content, or an empty string if an error occurs.
    """
    try:
        return elem.text.strip()
    except (NoSuchElementException, StaleElementReferenceException, AttributeError):
        return ""


def reject_cookies(driver, wait_timeout: int = 20) -> bool:
    """Attempts to click the 'Reject All' or 'Accept' (as fallback) button
    to close the cookie consent pop-up.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.
    wait_timeout : int, optional
        Maximum time in seconds to wait for the buttons to become clickable,
        defaults to 20.

    Returns
    -------
    bool
        True if the cookie pop-up was successfully closed by clicking either
        the reject or the fallback accept button, False otherwise.
    """
    wait = WebDriverWait(driver, wait_timeout)

    try:
        reject_button = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
        )
        reject_button.click()
        print("[INFO] Click the 'Reject All' button to remove cookies.")
        random_delay()
        return True
    except Exception:  # noqa: S110
        pass

    try:
        fallback_button = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        fallback_button.click()
        print("[INFO] Reject button not found. Clicked Accept (Fallback)")
        random_delay()
        return True
    except Exception:
        # Falha total: o pop-up não existe ou já foi fechado.
        print("[INFO] Consent pop-up not found or already closed.")
        return False


def handle_language_warning(driver) -> bool:
    """
    Attempts to click the 'Click here' link within the language warning banner.

    If successful, it waits for the main page content (h1) to load.

    Parameters
    ----------
    driver : WebDriver
        The active Selenium WebDriver instance.

    Returns
    -------
    bool
        True if the language warning link was successfully clicked and the
        page reloaded, False otherwise.
    """
    WAIT_SHORT = 5

    try:
        wait = WebDriverWait(driver, WAIT_SHORT)
        language_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class*='banner_'] a"))
        )

        if language_link:
            language_link.click()
            print("[INFO] Language warning link clicked. Language issue resolved.")

            WebDriverWait(driver, WAIT_SHORT).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            random_delay()
            return True

    except Exception:
        return False
