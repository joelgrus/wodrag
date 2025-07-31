"""Download CrossFit workout pages from crossfit.com."""

import logging
import time
from collections.abc import Iterator
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def generate_months(
    start_year: int, start_month: int, end_year: int, end_month: int
) -> Iterator[tuple[int, int]]:
    """Generate all (year, month) tuples in the given range.

    Args:
        start_year: Starting year
        start_month: Starting month (1-12)
        end_year: Ending year
        end_month: Ending month (1-12)

    Yields:
        Tuples of (year, month) for each month in the range
    """
    current_year = start_year
    current_month = start_month

    while (current_year < end_year) or (
        current_year == end_year and current_month <= end_month
    ):
        yield (current_year, current_month)

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1


def download_month(year: int, month: int, output_dir: Path, timeout: int = 30) -> bool:
    """Download a single month's workout HTML from crossfit.com.

    Args:
        year: Year to download
        month: Month to download (1-12)
        output_dir: Directory to save HTML files
        timeout: Request timeout in seconds

    Returns:
        True if download was successful, False otherwise
    """
    url = f"https://www.crossfit.com/workout/{year}/{month:02d}"
    filename = output_dir / f"{year}-{month:02d}.html"

    # Skip if file already exists
    if filename.exists():
        logger.info(f"Skipping {filename.name} - already exists")
        return True

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        logger.info(f"Downloading {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Save the HTML content
        filename.write_text(response.text, encoding="utf-8")
        logger.info(f"Saved {filename.name} ({len(response.text)} bytes)")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def download_all(
    output_dir: Path = Path("data/raw"),
    start_year: int = 2001,
    start_month: int = 2,
    end_year: int = 2025,
    end_month: int = 7,
    delay: float = 1.5,
) -> None:
    """Download all CrossFit workout pages in the specified range.

    Args:
        output_dir: Directory to save HTML files
        start_year: Starting year
        start_month: Starting month
        end_year: Ending year
        end_month: Ending month
        delay: Delay in seconds between requests
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    success_count = 0
    failure_count = 0
    skipped_count = 0

    logger.info(
        f"Starting download from {start_year}-{start_month:02d} "
        f"to {end_year}-{end_month:02d}"
    )

    for year, month in generate_months(start_year, start_month, end_year, end_month):
        filename = output_dir / f"{year}-{month:02d}.html"

        if filename.exists():
            skipped_count += 1
        elif download_month(year, month, output_dir):
            success_count += 1
            # Be polite to the server
            time.sleep(delay)
        else:
            failure_count += 1
            # Still wait even on failure
            time.sleep(delay)

    logger.info(
        f"Download complete: {success_count} successful, "
        f"{failure_count} failed, {skipped_count} skipped"
    )
