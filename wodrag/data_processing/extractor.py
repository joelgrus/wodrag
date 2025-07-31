"""Extract CrossFit workouts from HTML files."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from .simple_parser import parse_workout_simple

logger = logging.getLogger(__name__)


@dataclass
class Workout:
    """Represents a single CrossFit workout."""

    # Core fields
    date: str  # ISO format date string
    url: str
    raw_text: str  # Full original text

    # Parsed sections
    workout: str  # Core workout content (after date, before scaling/post)
    scaling: str | None = None  # Scaling/modification details

    # Simple metadata
    has_video: bool = False
    has_article: bool = False
    month_file: str = ""  # Source file (e.g., "2024-11.html")


def parse_date_header(date_text: str) -> str | None:
    """Parse date from header text like 'Saturday 241130' to ISO date."""
    try:
        # Remove day name and parse the date code
        parts = date_text.split()
        if len(parts) >= 2:
            date_code = parts[-1]  # e.g., "241130"
            if len(date_code) == 6:
                # Format: YYMMDD
                year = 2000 + int(date_code[:2])
                month = int(date_code[2:4])
                day = int(date_code[4:6])
                return f"{year:04d}-{month:02d}-{day:02d}"
    except (ValueError, IndexError):
        pass
    return None


def extract_workouts_from_file(file_path: Path) -> list[Workout]:
    """Extract all workouts from a single HTML file."""
    logger.info(f"Extracting workouts from {file_path.name}")
    workouts: list[Workout] = []

    try:
        with open(file_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Find the archives section
        archives = soup.find("section", id="archives")
        if not archives or not isinstance(archives, Tag):
            logger.warning(f"No archives section found in {file_path.name}")
            return workouts

        # Find the container
        container = archives.find("div", class_="container-hybrid")
        if not container or not isinstance(container, Tag):
            logger.warning(f"No container-hybrid found in {file_path.name}")
            return workouts

        # Extract each workout div
        workout_divs = container.find_all("div", recursive=False)

        for div in workout_divs:
            if not isinstance(div, Tag):
                continue

            # Skip empty divs or loader divs
            div_classes = div.get("class")
            if div_classes and "ajax-loader" in div_classes:
                continue

            # Extract date from h3 or h4
            date_elem = div.find(["h3", "h4"])
            if not date_elem or not isinstance(date_elem, Tag):
                continue

            date_text = date_elem.get_text(strip=True)
            iso_date = parse_date_header(date_text)

            if not iso_date:
                logger.warning(f"Could not parse date: {date_text}")
                continue

            # Extract workout URL
            url = ""
            links = div.find_all("a")
            for link in links:
                if not isinstance(link, Tag):
                    continue
                href = link.get("href", "")
                if isinstance(href, str) and "/workout/" in href and href not in url:
                    # Ensure full URL
                    if href.startswith("/"):
                        url = f"https://www.crossfit.com{href}"
                    else:
                        url = href
                    break

            # Extract raw text content
            raw_text = div.get_text(separator="\n", strip=True)

            # Check for videos and articles
            has_video = bool(div.find("iframe")) or "video" in raw_text.lower()
            has_article = "article" in raw_text.lower() or "journal" in raw_text.lower()

            # Parse workout content using the simple parser
            parsed_data = parse_workout_simple(raw_text)

            # Create workout object with parsed data
            workout_text = parsed_data["workout"]
            assert isinstance(workout_text, str)  # Always str from simple parser

            workout = Workout(
                date=iso_date,
                url=url,
                raw_text=raw_text,
                workout=workout_text,
                scaling=parsed_data["scaling"],
                has_video=has_video,
                has_article=has_article,
                month_file=file_path.name,
            )

            workouts.append(workout)

    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {e}")

    logger.info(f"Extracted {len(workouts)} workouts from {file_path.name}")
    return workouts


def extract_all_workouts(
    input_dir: Path = Path("data/raw"), output_dir: Path = Path("data/processed/json")
) -> None:
    """Extract workouts from all HTML files and save as JSON."""
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Process all HTML files
    html_files = sorted(input_dir.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files to process")

    total_workouts = 0

    for file_path in html_files:
        # Extract workouts
        workouts = extract_workouts_from_file(file_path)

        if workouts:
            # Convert to JSON-serializable format
            workouts_data = [asdict(w) for w in workouts]

            # Save to JSON file with same name
            output_file = output_dir / f"{file_path.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(workouts_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(workouts)} workouts to {output_file.name}")
            total_workouts += len(workouts)

    logger.info(f"Extraction complete: {total_workouts} total workouts extracted")


if __name__ == "__main__":
    extract_all_workouts()
