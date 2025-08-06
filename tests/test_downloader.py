"""Tests for the downloader module."""

from pathlib import Path
from unittest.mock import Mock, patch

from wodrag.data_processing.downloader import download_month, generate_months


class TestGenerateMonths:
    """Test the generate_months function."""

    def test_single_month(self) -> None:
        """Test generating a single month."""
        months = list(generate_months(2021, 1, 2021, 1))
        assert months == [(2021, 1)]

    def test_single_year(self) -> None:
        """Test generating months within a single year."""
        months = list(generate_months(2021, 3, 2021, 5))
        assert months == [(2021, 3), (2021, 4), (2021, 5)]

    def test_cross_year(self) -> None:
        """Test generating months across years."""
        months = list(generate_months(2020, 11, 2021, 2))
        assert months == [(2020, 11), (2020, 12), (2021, 1), (2021, 2)]

    def test_multiple_years(self) -> None:
        """Test generating months across multiple years."""
        months = list(generate_months(2019, 10, 2021, 3))
        assert len(months) == 18  # Oct 2019 to Mar 2021
        assert months[0] == (2019, 10)
        assert months[-1] == (2021, 3)


class TestDownloadMonth:
    """Test the download_month function."""

    @patch("wodrag.data_processing.downloader.requests.get")
    def test_successful_download(self, mock_get: Mock, tmp_path: Path) -> None:
        """Test successful download of a month."""
        # Mock response
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download
        result = download_month(2021, 3, tmp_path)

        # Check results
        assert result is True
        assert (tmp_path / "2021-03.html").exists()
        assert (tmp_path / "2021-03.html").read_text() == "<html>Test content</html>"

        # Verify request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://www.crossfit.com/workout/2021/03"
        assert "User-Agent" in call_args[1]["headers"]

    def test_skip_existing_file(self, tmp_path: Path) -> None:
        """Test that existing files are skipped."""
        # Create existing file
        existing_file = tmp_path / "2021-03.html"
        existing_file.write_text("Existing content")

        # Try to download
        result = download_month(2021, 3, tmp_path)

        # Should return True but not overwrite
        assert result is True
        assert existing_file.read_text() == "Existing content"

    @patch("wodrag.data_processing.downloader.requests.get")
    def test_download_failure(self, mock_get: Mock, tmp_path: Path) -> None:
        """Test handling of download failures."""
        # Mock failed request
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        # Download
        result = download_month(2021, 3, tmp_path)

        # Check results
        assert result is False
        assert not (tmp_path / "2021-03.html").exists()
