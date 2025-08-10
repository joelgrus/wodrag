#!/usr/bin/env python3
"""Script to download all CrossFit workout pages."""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import wodrag
sys.path.insert(0, str(Path(__file__).parent.parent))

from wodrag.data_processing.downloader import download_all


def main() -> None:
    """Run the download process."""

    # You can customize these parameters if needed
    download_all(
        output_dir=Path("data/raw"),
        start_year=2001,
        start_month=2,
        end_year=2025,
        end_month=7,
        delay=1.5,  # seconds between requests
    )


if __name__ == "__main__":
    main()
